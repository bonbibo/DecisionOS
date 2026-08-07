using System.Runtime.InteropServices;
using System.Text.Json.Serialization;

namespace TaskRecorder;

/// <summary>Global mouse/keyboard capture via Win32 low-level hooks (WH_MOUSE_LL / WH_KEYBOARD_LL).</summary>
public sealed class InputHook : IDisposable
{
    private const int WH_MOUSE_LL = 14;
    private const int WH_KEYBOARD_LL = 13;
    private const int WM_MOUSEMOVE = 0x0200;
    private const int WM_LBUTTONDOWN = 0x0201;
    private const int WM_LBUTTONUP = 0x0202;
    private const int WM_RBUTTONDOWN = 0x0204;
    private const int WM_RBUTTONUP = 0x0205;
    private const int WM_MBUTTONDOWN = 0x0207;
    private const int WM_MBUTTONUP = 0x0208;
    private const int WM_KEYDOWN = 0x0100;
    private const int WM_KEYUP = 0x0101;
    private const int WM_SYSKEYDOWN = 0x0104;
    private const int WM_SYSKEYUP = 0x0105;

    private readonly LowLevelProc _mouseProc;
    private readonly LowLevelProc _keyboardProc;
    private nint _mouseHookId;
    private nint _keyboardHookId;
    private readonly JsonlWriter _writer;

    // Throttle mouse_move events — a raw hook fires far more often than any downstream
    // consumer needs; we keep clicks/keys at full fidelity and sample movement.
    private static readonly TimeSpan MouseMoveInterval = TimeSpan.FromMilliseconds(1000.0 / 30.0);
    private DateTime _lastMouseMoveWrite = DateTime.MinValue;

    private delegate nint LowLevelProc(int nCode, nint wParam, nint lParam);

    public InputHook(JsonlWriter writer)
    {
        _writer = writer;
        _mouseProc = MouseHookCallback;
        _keyboardProc = KeyboardHookCallback;
    }

    public void Start()
    {
        using var curProcess = System.Diagnostics.Process.GetCurrentProcess();
        using var curModule = curProcess.MainModule!;
        var hModule = GetModuleHandle(curModule.ModuleName);
        _mouseHookId = SetWindowsHookEx(WH_MOUSE_LL, _mouseProc, hModule, 0);
        _keyboardHookId = SetWindowsHookEx(WH_KEYBOARD_LL, _keyboardProc, hModule, 0);
    }

    private nint MouseHookCallback(int nCode, nint wParam, nint lParam)
    {
        if (nCode >= 0)
        {
            var data = Marshal.PtrToStructure<MSLLHOOKSTRUCT>(lParam);
            var now = Timestamp.Now();

            switch ((int)wParam)
            {
                case WM_MOUSEMOVE:
                    var nowUtc = DateTime.UtcNow;
                    if (nowUtc - _lastMouseMoveWrite >= MouseMoveInterval)
                    {
                        _lastMouseMoveWrite = nowUtc;
                        _writer.WriteLine(new InputEvent { T = now, Type = "mouse_move", X = data.pt.x, Y = data.pt.y });
                    }
                    break;
                case WM_LBUTTONDOWN:
                    _writer.WriteLine(new InputEvent { T = now, Type = "mouse_down", X = data.pt.x, Y = data.pt.y, Button = "left" });
                    break;
                case WM_LBUTTONUP:
                    _writer.WriteLine(new InputEvent { T = now, Type = "mouse_up", X = data.pt.x, Y = data.pt.y, Button = "left" });
                    break;
                case WM_RBUTTONDOWN:
                    _writer.WriteLine(new InputEvent { T = now, Type = "mouse_down", X = data.pt.x, Y = data.pt.y, Button = "right" });
                    break;
                case WM_RBUTTONUP:
                    _writer.WriteLine(new InputEvent { T = now, Type = "mouse_up", X = data.pt.x, Y = data.pt.y, Button = "right" });
                    break;
                case WM_MBUTTONDOWN:
                    _writer.WriteLine(new InputEvent { T = now, Type = "mouse_down", X = data.pt.x, Y = data.pt.y, Button = "middle" });
                    break;
                case WM_MBUTTONUP:
                    _writer.WriteLine(new InputEvent { T = now, Type = "mouse_up", X = data.pt.x, Y = data.pt.y, Button = "middle" });
                    break;
            }
        }

        return CallNextHookEx(_mouseHookId, nCode, wParam, lParam);
    }

    private nint KeyboardHookCallback(int nCode, nint wParam, nint lParam)
    {
        if (nCode >= 0)
        {
            var data = Marshal.PtrToStructure<KBDLLHOOKSTRUCT>(lParam);
            var key = ((System.Windows.Forms.Keys)data.vkCode).ToString();
            var now = Timestamp.Now();
            var msg = (int)wParam;

            if (msg is WM_KEYDOWN or WM_SYSKEYDOWN)
            {
                var combo = ModifierState.CurrentCombo(key);
                _writer.WriteLine(new InputEvent { T = now, Type = "key_down", Key = key, Combo = combo });
            }
            else if (msg is WM_KEYUP or WM_SYSKEYUP)
            {
                _writer.WriteLine(new InputEvent { T = now, Type = "key_up", Key = key });
            }
        }

        return CallNextHookEx(_keyboardHookId, nCode, wParam, lParam);
    }

    public void Dispose()
    {
        if (_mouseHookId != 0) UnhookWindowsHookEx(_mouseHookId);
        if (_keyboardHookId != 0) UnhookWindowsHookEx(_keyboardHookId);
    }

    [StructLayout(LayoutKind.Sequential)]
    private struct POINT { public int x; public int y; }

    [StructLayout(LayoutKind.Sequential)]
    private struct MSLLHOOKSTRUCT
    {
        public POINT pt;
        public uint mouseData;
        public uint flags;
        public uint time;
        public nint dwExtraInfo;
    }

    [StructLayout(LayoutKind.Sequential)]
    private struct KBDLLHOOKSTRUCT
    {
        public uint vkCode;
        public uint scanCode;
        public uint flags;
        public uint time;
        public nint dwExtraInfo;
    }

    [DllImport("user32.dll", CharSet = CharSet.Auto, SetLastError = true)]
    private static extern nint SetWindowsHookEx(int idHook, LowLevelProc lpfn, nint hMod, uint dwThreadId);

    [DllImport("user32.dll", CharSet = CharSet.Auto, SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool UnhookWindowsHookEx(nint hhk);

    [DllImport("user32.dll", CharSet = CharSet.Auto, SetLastError = true)]
    private static extern nint CallNextHookEx(nint hhk, int nCode, nint wParam, nint lParam);

    [DllImport("kernel32.dll", CharSet = CharSet.Auto, SetLastError = true)]
    private static extern nint GetModuleHandle(string? lpModuleName);
}

/// <summary>Tracks Ctrl/Alt/Shift/Win modifier state so key_down events can carry a "combo" (shortcut).</summary>
internal static class ModifierState
{
    public static string[] CurrentCombo(string key)
    {
        var mods = new List<string>();
        if (IsDown(0x11)) mods.Add("Ctrl");   // VK_CONTROL
        if (IsDown(0x12)) mods.Add("Alt");    // VK_MENU
        if (IsDown(0x10)) mods.Add("Shift");  // VK_SHIFT
        if (IsDown(0x5B) || IsDown(0x5C)) mods.Add("Win"); // VK_LWIN / VK_RWIN

        if (!mods.Contains(key))
        {
            mods.Add(key);
        }
        return mods.ToArray();
    }

    private static bool IsDown(int vk) => (GetKeyState(vk) & 0x8000) != 0;

    [DllImport("user32.dll")]
    private static extern short GetKeyState(int nVirtKey);
}

internal static class Timestamp
{
    /// <summary>Unix epoch seconds as a double, matching input_events.jsonl / unity_events.jsonl "t" field.</summary>
    public static double Now() => DateTimeOffset.UtcNow.ToUnixTimeMilliseconds() / 1000.0;
}

public sealed class InputEvent
{
    [JsonPropertyName("t")] public double T { get; set; }
    [JsonPropertyName("type")] public string Type { get; set; } = "";
    [JsonPropertyName("x")] public int? X { get; set; }
    [JsonPropertyName("y")] public int? Y { get; set; }
    [JsonPropertyName("button")] public string? Button { get; set; }
    [JsonPropertyName("key")] public string? Key { get; set; }
    [JsonPropertyName("combo")] public string[]? Combo { get; set; }
}

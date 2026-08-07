using System.Text.Json;

namespace TaskRecorder;

internal static class Program
{
    [STAThread]
    private static void Main(string[] args)
    {
        ApplicationConfiguration.Initialize();

        var config = LoadConfig();
        Application.Run(new MainForm(config));
    }

    /// <summary>
    /// Reads recorder.config.json next to the executable if present, otherwise falls back
    /// to defaults. Kept as plain JSON (no env vars, no secrets) — this tool never handles
    /// credentials beyond an optional local OBS websocket password.
    /// </summary>
    private static RecorderConfig LoadConfig()
    {
        var configPath = Path.Combine(AppContext.BaseDirectory, "recorder.config.json");
        if (!File.Exists(configPath))
        {
            return new RecorderConfig();
        }

        try
        {
            var json = File.ReadAllText(configPath);
            return JsonSerializer.Deserialize<RecorderConfig>(json) ?? new RecorderConfig();
        }
        catch (JsonException)
        {
            return new RecorderConfig();
        }
    }
}

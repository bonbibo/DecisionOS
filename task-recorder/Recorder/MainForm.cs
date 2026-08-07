using System.Text.Json;

namespace TaskRecorder;

/// <summary>
/// System-tray shell around TaskSession/InputHook/ObsClient. All the real logic lives in
/// those classes; this form is just Start/Stop wiring + two prompt dialogs.
/// </summary>
public sealed class MainForm : Form
{
    private readonly NotifyIcon _tray;
    private readonly RecorderConfig _config;

    private TaskSession? _session;
    private InputHook? _inputHook;
    private JsonlWriter? _inputWriter;
    private ObsClient? _obs;

    public MainForm(RecorderConfig config)
    {
        _config = config;
        Directory.CreateDirectory(_config.RecordingsRoot);
        TaskSession.RecoverIncomplete(_config.RecordingsRoot);

        WindowState = FormWindowState.Minimized;
        ShowInTaskbar = false;

        var menu = new ContextMenuStrip();
        var startItem = menu.Items.Add("Start Task");
        var stopItem = menu.Items.Add("Stop Task");
        menu.Items.Add(new ToolStripSeparator());
        var exitItem = menu.Items.Add("Exit");

        stopItem.Enabled = false;

        startItem.Click += async (_, _) =>
        {
            if (_session is not null) return;
            await StartTaskAsync();
            startItem.Enabled = false;
            stopItem.Enabled = true;
        };

        stopItem.Click += async (_, _) =>
        {
            if (_session is null) return;
            await StopTaskAsync();
            startItem.Enabled = true;
            stopItem.Enabled = false;
        };

        exitItem.Click += (_, _) => Close();

        _tray = new NotifyIcon
        {
            Icon = System.Drawing.SystemIcons.Application,
            Visible = true,
            ContextMenuStrip = menu,
            Text = "Task Recorder",
        };
    }

    private async Task StartTaskAsync()
    {
        var description = Prompt.Show("Görev açıklaması:", "Start Task");
        if (description is null)
        {
            return; // user cancelled
        }

        _session = TaskSession.Start(_config.RecordingsRoot, description, _config.RepoPath);

        // Drop the pointer the Unity plugin reads to know where to write unity_events.jsonl.
        var pointerPath = Path.Combine(_config.RepoPath, "session_pointer.json");
        try
        {
            File.WriteAllText(pointerPath, JsonSerializer.Serialize(new { task_folder = _session.TaskFolder }));
        }
        catch (IOException)
        {
            // Repo path not writable / doesn't exist — Unity events are lost for this task,
            // but input + video + git capture still work, so we don't abort the task.
        }

        _inputWriter = new JsonlWriter(_session.PathFor("input_events.jsonl"));
        _inputHook = new InputHook(_inputWriter);
        _inputHook.Start();

        if (_config.ObsEnabled)
        {
            _obs = new ObsClient(_config.ObsHost, _config.ObsPort, _config.ObsPassword);
            try
            {
                await _obs.ConnectAsync();
                await _obs.StartRecordAsync();
            }
            catch (Exception ex)
            {
                MessageBox.Show(this, $"OBS'e bağlanılamadı, ekran kaydı olmadan devam ediliyor:\n{ex.Message}",
                    "Task Recorder", MessageBoxButtons.OK, MessageBoxIcon.Warning);
            }
        }

        _tray.ShowBalloonTip(2000, "Task Recorder", $"Görev başladı: {_session.Meta.TaskId}", ToolTipIcon.Info);
    }

    private async Task StopTaskAsync()
    {
        if (_session is null) return;

        string? videoPath = null;
        if (_obs is not null)
        {
            try
            {
                videoPath = await _obs.StopRecordAsync();
                await _obs.DisposeAsync();
            }
            catch (Exception ex)
            {
                MessageBox.Show(this, $"OBS kaydı durdurulamadı:\n{ex.Message}",
                    "Task Recorder", MessageBoxButtons.OK, MessageBoxIcon.Warning);
            }
            _obs = null;
        }

        _inputHook?.Dispose();
        _inputHook = null;
        _inputWriter?.Dispose();
        _inputWriter = null;

        if (!string.IsNullOrEmpty(videoPath) && File.Exists(videoPath))
        {
            var dest = _session.PathFor("screen" + Path.GetExtension(videoPath));
            try
            {
                File.Move(videoPath, dest);
            }
            catch (IOException)
            {
                // Cross-volume move or file still locked by OBS's finalize step — leave the
                // video where OBS put it rather than losing the recording.
            }
        }

        var (status, note) = SuccessPrompt.Show();
        _session.Stop(status, note);

        _tray.ShowBalloonTip(2000, "Task Recorder", $"Görev kaydedildi: {_session.Meta.TaskId}", ToolTipIcon.Info);
        _session = null;
    }

    protected override void Dispose(bool disposing)
    {
        if (disposing)
        {
            _inputHook?.Dispose();
            _inputWriter?.Dispose();
            _tray.Visible = false;
            _tray.Dispose();
        }
        base.Dispose(disposing);
    }
}

public sealed class RecorderConfig
{
    public string RecordingsRoot { get; set; } = @"D:\TaskRecordings";
    public string RepoPath { get; set; } = "";
    public bool ObsEnabled { get; set; } = true;
    public string ObsHost { get; set; } = "localhost";
    public int ObsPort { get; set; } = 4455;
    public string? ObsPassword { get; set; }
}

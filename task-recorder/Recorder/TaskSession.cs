using System.Text.Json;
using System.Text.Json.Serialization;

namespace TaskRecorder;

public enum SuccessStatus
{
    success,
    partial,
    failed,
    incomplete,
}

public sealed class TaskMeta
{
    [JsonPropertyName("task_id")] public string TaskId { get; set; } = "";
    [JsonPropertyName("description")] public string Description { get; set; } = "";
    [JsonPropertyName("repo_path")] public string RepoPath { get; set; } = "";
    [JsonPropertyName("started_at")] public DateTimeOffset StartedAt { get; set; }
    [JsonPropertyName("ended_at")] public DateTimeOffset? EndedAt { get; set; }
    [JsonPropertyName("success")] public string Success { get; set; } = SuccessStatus.incomplete.ToString();
    [JsonPropertyName("success_note")] public string? SuccessNote { get; set; }
    [JsonPropertyName("recorder_version")] public string RecorderVersion { get; set; } = "0.1.0";
}

/// <summary>
/// Owns the lifecycle of one recorded task: folder creation, task.json / git_meta.json
/// persistence, and the crash-recovery marker. Does not itself touch OBS or input hooks —
/// MainForm wires those to Start()/Stop().
/// </summary>
public sealed class TaskSession
{
    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        WriteIndented = true,
    };

    public string RootDir { get; }
    public string TaskFolder { get; }
    public TaskMeta Meta { get; }

    private TaskSession(string rootDir, string taskFolder, TaskMeta meta)
    {
        RootDir = rootDir;
        TaskFolder = taskFolder;
        Meta = meta;
    }

    public static TaskSession Start(string recordingsRoot, string description, string repoPath)
    {
        var startedAt = DateTimeOffset.Now;
        var slug = Slugify(description);
        var taskId = $"{startedAt:yyyyMMdd-HHmmss}_{slug}";
        var folder = Path.Combine(recordingsRoot, taskId);
        Directory.CreateDirectory(folder);

        var meta = new TaskMeta
        {
            TaskId = taskId,
            Description = description,
            RepoPath = repoPath,
            StartedAt = startedAt,
            Success = SuccessStatus.incomplete.ToString(),
        };

        var session = new TaskSession(recordingsRoot, folder, meta);
        session.WriteMeta();

        // Crash-recovery marker: presence of this file with no matching "ended_at" in
        // task.json means the app died mid-task. See RecoverIncomplete().
        File.WriteAllText(Path.Combine(folder, ".in_progress"), startedAt.ToString("O"));

        GitDiffCapture.SnapshotStart(repoPath, folder);

        return session;
    }

    public void Stop(SuccessStatus status, string? note)
    {
        Meta.EndedAt = DateTimeOffset.Now;
        Meta.Success = status.ToString();
        Meta.SuccessNote = note;
        WriteMeta();

        GitDiffCapture.SnapshotEnd(Meta.RepoPath, TaskFolder);

        var marker = Path.Combine(TaskFolder, ".in_progress");
        if (File.Exists(marker))
        {
            File.Delete(marker);
        }
    }

    public string PathFor(string fileName) => Path.Combine(TaskFolder, fileName);

    private void WriteMeta()
    {
        var json = JsonSerializer.Serialize(Meta, JsonOptions);
        File.WriteAllText(Path.Combine(TaskFolder, "task.json"), json);
    }

    /// <summary>
    /// Call on app startup. Any task folder still carrying ".in_progress" means Stop() was
    /// never called (crash / force-quit) — mark it incomplete rather than silently losing
    /// the "was this task ever finished?" signal.
    /// </summary>
    public static void RecoverIncomplete(string recordingsRoot)
    {
        if (!Directory.Exists(recordingsRoot))
        {
            return;
        }

        foreach (var folder in Directory.GetDirectories(recordingsRoot))
        {
            var marker = Path.Combine(folder, ".in_progress");
            var taskJsonPath = Path.Combine(folder, "task.json");
            if (!File.Exists(marker) || !File.Exists(taskJsonPath))
            {
                continue;
            }

            var meta = JsonSerializer.Deserialize<TaskMeta>(File.ReadAllText(taskJsonPath));
            if (meta is null)
            {
                continue;
            }

            meta.Success = SuccessStatus.incomplete.ToString();
            meta.EndedAt ??= DateTimeOffset.Now;
            File.WriteAllText(taskJsonPath, JsonSerializer.Serialize(meta, JsonOptions));
            File.Delete(marker);
        }
    }

    private static string Slugify(string description)
    {
        if (string.IsNullOrWhiteSpace(description))
        {
            return "task";
        }

        var chars = description.Trim().ToLowerInvariant()
            .Select(c => char.IsLetterOrDigit(c) ? c : '-')
            .ToArray();
        var slug = new string(chars);
        while (slug.Contains("--"))
        {
            slug = slug.Replace("--", "-");
        }
        slug = slug.Trim('-');
        return slug.Length > 40 ? slug[..40] : (slug.Length == 0 ? "task" : slug);
    }
}

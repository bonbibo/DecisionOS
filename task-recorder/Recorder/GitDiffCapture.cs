using System.Diagnostics;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace TaskRecorder;

public sealed class GitMeta
{
    [JsonPropertyName("branch")] public string? Branch { get; set; }
    [JsonPropertyName("start_commit")] public string? StartCommit { get; set; }
    [JsonPropertyName("end_commit")] public string? EndCommit { get; set; }
    [JsonPropertyName("start_dirty")] public bool StartDirty { get; set; }
    [JsonPropertyName("end_dirty")] public bool EndDirty { get; set; }
}

/// <summary>
/// Shells out to the git CLI to snapshot repo state at task start and end. Deliberately
/// dumb (no libgit2 dependency) — this only needs to run twice per task, not on a hot path.
/// If <paramref name="repoPath"/> is not a git repo, every call becomes a no-op and
/// git_meta.json simply carries nulls; a task recording must never fail because the target
/// folder isn't version-controlled.
/// </summary>
public static class GitDiffCapture
{
    private static readonly JsonSerializerOptions JsonOptions = new() { WriteIndented = true };

    public static void SnapshotStart(string repoPath, string taskFolder)
    {
        var meta = ReadMeta(taskFolder) ?? new GitMeta();
        meta.Branch = RunGit(repoPath, "rev-parse --abbrev-ref HEAD");
        meta.StartCommit = RunGit(repoPath, "rev-parse HEAD");
        var diff = RunGit(repoPath, "diff HEAD");
        meta.StartDirty = !string.IsNullOrWhiteSpace(diff);
        if (diff is not null)
        {
            File.WriteAllText(Path.Combine(taskFolder, "git_diff_start.patch"), diff);
        }
        WriteMeta(taskFolder, meta);
    }

    public static void SnapshotEnd(string repoPath, string taskFolder)
    {
        var meta = ReadMeta(taskFolder) ?? new GitMeta();
        meta.EndCommit = RunGit(repoPath, "rev-parse HEAD");
        var diff = RunGit(repoPath, "diff HEAD");
        meta.EndDirty = !string.IsNullOrWhiteSpace(diff);
        if (diff is not null)
        {
            File.WriteAllText(Path.Combine(taskFolder, "git_diff_end.patch"), diff);
        }
        WriteMeta(taskFolder, meta);
    }

    private static GitMeta? ReadMeta(string taskFolder)
    {
        var path = Path.Combine(taskFolder, "git_meta.json");
        return File.Exists(path)
            ? JsonSerializer.Deserialize<GitMeta>(File.ReadAllText(path))
            : null;
    }

    private static void WriteMeta(string taskFolder, GitMeta meta)
    {
        File.WriteAllText(Path.Combine(taskFolder, "git_meta.json"), JsonSerializer.Serialize(meta, JsonOptions));
    }

    /// <summary>Runs `git &lt;args&gt;` in repoPath. Returns null if git/repo is unavailable.</summary>
    private static string? RunGit(string repoPath, string args)
    {
        if (string.IsNullOrWhiteSpace(repoPath) || !Directory.Exists(repoPath))
        {
            return null;
        }

        try
        {
            var psi = new ProcessStartInfo("git", args)
            {
                WorkingDirectory = repoPath,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                UseShellExecute = false,
                CreateNoWindow = true,
            };
            using var process = Process.Start(psi);
            if (process is null)
            {
                return null;
            }

            var stdout = process.StandardOutput.ReadToEnd();
            process.WaitForExit(10_000);
            return process.ExitCode == 0 ? stdout.Trim() : null;
        }
        catch (Exception)
        {
            // git not installed, not a repo, permission issue, etc. — the task recording
            // must still proceed without git metadata.
            return null;
        }
    }
}

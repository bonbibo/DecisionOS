using System.Text;
using System.Text.Json;

namespace TaskRecorder;

/// <summary>
/// Append-only JSON-lines writer. Every line is flushed to disk immediately so a crash
/// loses at most the in-flight write, never buffered history.
/// </summary>
public sealed class JsonlWriter : IDisposable
{
    private readonly StreamWriter _writer;
    private readonly object _lock = new();

    public JsonlWriter(string path)
    {
        var stream = new FileStream(path, FileMode.Append, FileAccess.Write, FileShare.Read);
        _writer = new StreamWriter(stream, new UTF8Encoding(encoderShouldEmitUTF8Identifier: false))
        {
            AutoFlush = false,
        };
    }

    public void WriteLine<T>(T value)
    {
        var json = JsonSerializer.Serialize(value);
        lock (_lock)
        {
            _writer.WriteLine(json);
            _writer.Flush();
        }
    }

    public void Dispose()
    {
        lock (_lock)
        {
            _writer.Flush();
            _writer.Dispose();
        }
    }
}

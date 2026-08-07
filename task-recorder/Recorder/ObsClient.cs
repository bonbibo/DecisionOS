using System.Net.WebSockets;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;

namespace TaskRecorder;

/// <summary>
/// Minimal obs-websocket v5 client: just enough to start/stop recording and read back the
/// output file path. Not a general-purpose OBS SDK — Task Recorder needs exactly two
/// requests, so this stays a single small file instead of pulling in a NuGet dependency.
/// Protocol: https://github.com/obsproject/obs-websocket/blob/master/docs/generated/protocol.md
/// </summary>
public sealed class ObsClient : IAsyncDisposable
{
    private ClientWebSocket? _ws;
    private readonly Uri _uri;
    private readonly string? _password;

    public ObsClient(string host = "localhost", int port = 4455, string? password = null)
    {
        _uri = new Uri($"ws://{host}:{port}");
        _password = password;
    }

    public async Task ConnectAsync(CancellationToken ct = default)
    {
        _ws = new ClientWebSocket();
        await _ws.ConnectAsync(_uri, ct);

        // Op 0: Hello
        var hello = await ReceiveJsonAsync(ct);
        var d = hello["d"]!;

        var identify = new JsonObject
        {
            ["op"] = 1,
            ["d"] = new JsonObject
            {
                ["rpcVersion"] = d["rpcVersion"]?.GetValue<int>() ?? 1,
            },
        };

        if (d["authentication"] is JsonObject auth && !string.IsNullOrEmpty(_password))
        {
            var challenge = auth["challenge"]!.GetValue<string>();
            var salt = auth["salt"]!.GetValue<string>();
            var authResponse = ComputeAuth(_password, salt, challenge);
            ((JsonObject)identify["d"]!)["authentication"] = authResponse;
        }

        await SendJsonAsync(identify, ct);

        // Op 2: Identified
        await ReceiveJsonAsync(ct);
    }

    /// <summary>Starts OBS recording. Returns once OBS has acknowledged the request.</summary>
    public Task StartRecordAsync(CancellationToken ct = default) => CallAsync("StartRecord", null, ct);

    /// <summary>Stops OBS recording and returns the absolute path OBS wrote the file to.</summary>
    public async Task<string?> StopRecordAsync(CancellationToken ct = default)
    {
        var response = await CallAsync("StopRecord", null, ct);
        return response?["responseData"]?["outputPath"]?.GetValue<string>();
    }

    private async Task<JsonObject?> CallAsync(string requestType, JsonObject? requestData, CancellationToken ct)
    {
        var requestId = Guid.NewGuid().ToString("N");
        var request = new JsonObject
        {
            ["op"] = 6,
            ["d"] = new JsonObject
            {
                ["requestType"] = requestType,
                ["requestId"] = requestId,
                ["requestData"] = requestData,
            },
        };
        await SendJsonAsync(request, ct);

        // In principle other traffic could interleave; for our two sequential calls this
        // simple "next message is the response" read is sufficient.
        var response = await ReceiveJsonAsync(ct);
        return response["d"] as JsonObject;
    }

    private static string ComputeAuth(string password, string salt, string challenge)
    {
        using var sha256 = SHA256.Create();
        var secretBytes = sha256.ComputeHash(Encoding.UTF8.GetBytes(password + salt));
        var secret = Convert.ToBase64String(secretBytes);
        var authBytes = sha256.ComputeHash(Encoding.UTF8.GetBytes(secret + challenge));
        return Convert.ToBase64String(authBytes);
    }

    private async Task SendJsonAsync(JsonNode node, CancellationToken ct)
    {
        var bytes = Encoding.UTF8.GetBytes(node.ToJsonString());
        await _ws!.SendAsync(bytes, WebSocketMessageType.Text, endOfMessage: true, ct);
    }

    private async Task<JsonObject> ReceiveJsonAsync(CancellationToken ct)
    {
        var buffer = new byte[64 * 1024];
        var sb = new StringBuilder();
        WebSocketReceiveResult result;
        do
        {
            result = await _ws!.ReceiveAsync(buffer, ct);
            sb.Append(Encoding.UTF8.GetString(buffer, 0, result.Count));
        } while (!result.EndOfMessage);

        return JsonNode.Parse(sb.ToString())!.AsObject();
    }

    public async ValueTask DisposeAsync()
    {
        if (_ws is { State: WebSocketState.Open })
        {
            await _ws.CloseAsync(WebSocketCloseStatus.NormalClosure, "done", CancellationToken.None);
        }
        _ws?.Dispose();
    }
}

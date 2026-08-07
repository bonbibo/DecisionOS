// Task Recorder — Unity Editor bridge.
//
// Place this file under an "Editor/" folder anywhere in the Unity project (Unity only
// compiles it for the editor, never into player builds). It has no runtime footprint and
// no dependency on the Recorder app beyond a shared JSON pointer file — see
// docs/FORMAT.md's `session_pointer.json`.
//
// Responsibilities:
//   1. Watch for session_pointer.json appearing/changing in the project root (dropped by
//      the Recorder app on Start Task) and (re)open unity_events.jsonl in that task folder.
//   2. Forward EditorApplication/EditorSceneManager/CompilationPipeline events.
//   3. Forward Console log messages (Application.logMessageReceived).
//
// No compilation was possible in the environment this was written in (no Unity install) —
// review against your Unity/editor version before relying on it; the EditorApplication/
// CompilationPipeline event surface has shifted across Unity versions.

using System;
using System.IO;
using System.Text;
using UnityEditor;
using UnityEditor.Compilation;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace TaskRecorder.UnityBridge
{
    [InitializeOnLoad]
    public static class TaskRecorderBridge
    {
        private const string PointerFileName = "session_pointer.json";
        private static string _currentTaskFolder;
        private static StreamWriter _writer;
        private static readonly object WriteLock = new object();

        static TaskRecorderBridge()
        {
            EditorApplication.update += PollForPointerChange;
            EditorApplication.playModeStateChanged += OnPlayModeStateChanged;
            EditorSceneManager.sceneOpened += (scene, mode) => WriteEvent("scene_opened", new SceneEventData { scene = scene.path });
            EditorSceneManager.sceneClosed += scene => WriteEvent("scene_closed", new SceneEventData { scene = scene.path });
            CompilationPipeline.compilationStarted += _ => WriteEvent("compile_started", null);
            CompilationPipeline.compilationFinished += _ => WriteEvent("compile_finished", null);
            CompilationPipeline.assemblyCompilationFinished += OnAssemblyCompilationFinished;
            Application.logMessageReceived += OnLogMessageReceived;
        }

        private static double _lastPointerCheck;

        /// <summary>
        /// Polled instead of using a FileSystemWatcher: editor scripts run inside Unity's
        /// own update loop already, and polling once a second is simpler than wiring a
        /// watcher's lifetime to domain reloads.
        /// </summary>
        private static void PollForPointerChange()
        {
            var now = EditorApplication.timeSinceStartup;
            if (now - _lastPointerCheck < 1.0)
            {
                return;
            }
            _lastPointerCheck = now;

            var pointerPath = Path.Combine(GetProjectRoot(), PointerFileName);
            if (!File.Exists(pointerPath))
            {
                return;
            }

            try
            {
                var json = File.ReadAllText(pointerPath);
                var pointer = JsonUtility.FromJson<SessionPointer>(json);
                if (pointer == null || string.IsNullOrEmpty(pointer.task_folder))
                {
                    return;
                }

                if (pointer.task_folder != _currentTaskFolder)
                {
                    OpenTaskFolder(pointer.task_folder);
                }
            }
            catch (Exception ex)
            {
                Debug.LogWarning($"[TaskRecorder] session_pointer.json okunamadı: {ex.Message}");
            }
        }

        private static void OpenTaskFolder(string taskFolder)
        {
            lock (WriteLock)
            {
                _writer?.Dispose();
                _writer = null;

                if (!Directory.Exists(taskFolder))
                {
                    Debug.LogWarning($"[TaskRecorder] görev klasörü yok: {taskFolder}");
                    _currentTaskFolder = null;
                    return;
                }

                var path = Path.Combine(taskFolder, "unity_events.jsonl");
                _writer = new StreamWriter(new FileStream(path, FileMode.Append, FileAccess.Write, FileShare.Read), new UTF8Encoding(false))
                {
                    AutoFlush = true,
                };
                _currentTaskFolder = taskFolder;
            }
        }

        private static void OnPlayModeStateChanged(PlayModeStateChange state)
        {
            WriteEvent("play_mode_changed", new PlayModeEventData { state = state.ToString() });
        }

        private static void OnAssemblyCompilationFinished(string assemblyPath, CompilerMessage[] messages)
        {
            int warnings = 0, errors = 0;
            foreach (var m in messages)
            {
                if (m.type == CompilerMessageType.Warning) warnings++;
                else if (m.type == CompilerMessageType.Error) errors++;
            }
            WriteEvent("assembly_compiled", new CompileEventData { assembly = assemblyPath, warnings = warnings, errors = errors });
        }

        private static void OnLogMessageReceived(string condition, string stackTrace, LogType type)
        {
            WriteEvent("console_log", new ConsoleLogEventData
            {
                level = type.ToString(),
                message = condition,
                stack_trace = stackTrace,
            });
        }

        private static void WriteEvent(string type, object data)
        {
            lock (WriteLock)
            {
                if (_writer == null)
                {
                    return; // no active task — drop the event rather than buffering it
                }

                var envelope = new EventEnvelope
                {
                    t = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds() / 1000.0,
                    type = type,
                };
                var line = JsonUtility.ToJson(envelope);
                if (data != null)
                {
                    // JsonUtility can't merge objects, so we hand-splice: envelope JSON ends
                    // in "}", the payload's starts with "{" — strip the outer braces of the
                    // payload and stitch them into one flat object.
                    var payloadJson = JsonUtility.ToJson(data);
                    var innerFields = payloadJson.Substring(1, payloadJson.Length - 2);
                    if (innerFields.Length > 0)
                    {
                        line = line.Substring(0, line.Length - 1) + "," + innerFields + "}";
                    }
                }

                try
                {
                    _writer.WriteLine(line);
                }
                catch (IOException ex)
                {
                    Debug.LogWarning($"[TaskRecorder] unity_events.jsonl yazılamadı: {ex.Message}");
                }
            }
        }

        private static string GetProjectRoot()
        {
            // Application.dataPath is "<project>/Assets"; the pointer file lives one level up.
            return Directory.GetParent(Application.dataPath).FullName;
        }

        [Serializable]
        private class SessionPointer
        {
            public string task_folder;
        }

        [Serializable]
        private class EventEnvelope
        {
            public double t;
            public string type;
        }

        [Serializable]
        private class SceneEventData
        {
            public string scene;
        }

        [Serializable]
        private class PlayModeEventData
        {
            public string state;
        }

        [Serializable]
        private class CompileEventData
        {
            public string assembly;
            public int warnings;
            public int errors;
        }

        [Serializable]
        private class ConsoleLogEventData
        {
            public string level;
            public string message;
            public string stack_trace;
        }
    }
}

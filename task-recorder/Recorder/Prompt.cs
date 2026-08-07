namespace TaskRecorder;

/// <summary>Tiny modal text-input dialog — avoids pulling in a UI framework for one text box.</summary>
internal static class Prompt
{
    public static string? Show(string label, string title)
    {
        using var form = new Form
        {
            Text = title,
            Width = 420,
            Height = 150,
            FormBorderStyle = FormBorderStyle.FixedDialog,
            StartPosition = FormStartPosition.CenterScreen,
            MinimizeBox = false,
            MaximizeBox = false,
        };
        var lbl = new Label { Left = 12, Top = 12, Width = 380, Text = label };
        var textBox = new TextBox { Left = 12, Top = 36, Width = 380 };
        var ok = new Button { Text = "Tamam", Left = 232, Width = 80, Top = 70, DialogResult = DialogResult.OK };
        var cancel = new Button { Text = "İptal", Left = 316, Width = 80, Top = 70, DialogResult = DialogResult.Cancel };
        form.Controls.Add(lbl);
        form.Controls.Add(textBox);
        form.Controls.Add(ok);
        form.Controls.Add(cancel);
        form.AcceptButton = ok;
        form.CancelButton = cancel;

        return form.ShowDialog() == DialogResult.OK ? textBox.Text : null;
    }
}

/// <summary>Modal dialog for Stop Task: success enum + optional note.</summary>
internal static class SuccessPrompt
{
    public static (SuccessStatus status, string? note) Show()
    {
        using var form = new Form
        {
            Text = "Stop Task",
            Width = 420,
            Height = 200,
            FormBorderStyle = FormBorderStyle.FixedDialog,
            StartPosition = FormStartPosition.CenterScreen,
            MinimizeBox = false,
            MaximizeBox = false,
        };
        var lbl = new Label { Left = 12, Top = 12, Width = 380, Text = "Sonuç:" };
        var combo = new ComboBox
        {
            Left = 12,
            Top = 36,
            Width = 380,
            DropDownStyle = ComboBoxStyle.DropDownList,
        };
        combo.Items.AddRange(new object[] { "success", "partial", "failed" });
        combo.SelectedIndex = 0;

        var noteLbl = new Label { Left = 12, Top = 68, Width = 380, Text = "Not (opsiyonel):" };
        var noteBox = new TextBox { Left = 12, Top = 92, Width = 380 };

        var ok = new Button { Text = "Tamam", Left = 232, Width = 80, Top = 124, DialogResult = DialogResult.OK };
        var cancel = new Button { Text = "İptal", Left = 316, Width = 80, Top = 124, DialogResult = DialogResult.Cancel };
        form.Controls.Add(lbl);
        form.Controls.Add(combo);
        form.Controls.Add(noteLbl);
        form.Controls.Add(noteBox);
        form.Controls.Add(ok);
        form.Controls.Add(cancel);
        form.AcceptButton = ok;
        form.CancelButton = cancel;

        var result = form.ShowDialog();
        if (result != DialogResult.OK)
        {
            // Cancel doesn't abort Stop — a task is still finishing, we just default to
            // "partial" rather than forcing the user through the dialog again.
            return (SuccessStatus.partial, null);
        }

        var status = Enum.Parse<SuccessStatus>((string)combo.SelectedItem!);
        var note = string.IsNullOrWhiteSpace(noteBox.Text) ? null : noteBox.Text;
        return (status, note);
    }
}

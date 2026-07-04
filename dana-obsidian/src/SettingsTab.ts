import { App, Notice, PluginSettingTab, Setting } from 'obsidian';
import type DanaPlugin from '../main';

export class DanaSettingsTab extends PluginSettingTab {
  constructor(app: App, private plugin: DanaPlugin) {
    super(app, plugin);
  }

  display(): void {
    const { containerEl } = this;
    containerEl.empty();
    containerEl.addClass('dana-settings');

    // ── Journal folder ──────────────────────────────────────────────────
    new Setting(containerEl)
      .setName('Journal folder')
      .setDesc('The folder where your journal notes live. Leave empty to search the whole vault.')
      .addText(text =>
        text
          .setPlaceholder('Daily Notes')
          .setValue(this.plugin.settings.journalFolder)
          .onChange(async value => {
            this.plugin.settings.journalFolder = value.trim();
            await this.plugin.saveSettings();
          })
      );

    new Setting(containerEl)
      .setName('Notes to read')
      .setDesc('How many recent journal entries Dana reads for context (3–30).')
      .addDropdown(drop =>
        drop
          .addOption('3', 'Last 3 entries')
          .addOption('7', 'Last 7 entries')
          .addOption('14', 'Last 14 entries')
          .addOption('30', 'Last 30 entries')
          .setValue(String(this.plugin.settings.maxContextEntries))
          .onChange(async value => {
            this.plugin.settings.maxContextEntries = parseInt(value);
            await this.plugin.saveSettings();
          })
      );

    // ── AI setup ────────────────────────────────────────────────────────
    containerEl.createEl('h3', { text: 'AI Setup' });

    new Setting(containerEl)
      .setName('AI provider')
      .setDesc('How Dana thinks. Ollama runs entirely on your device. OpenAI requires an API key.')
      .addDropdown(drop =>
        drop
          .addOption('ollama', 'Ollama (local — recommended)')
          .addOption('openai', 'OpenAI')
          .setValue(this.plugin.settings.preferredProvider)
          .onChange(async (value: 'ollama' | 'openai') => {
            this.plugin.settings.preferredProvider = value;
            await this.plugin.saveSettings();
            this.display();
          })
      );

    if (this.plugin.settings.preferredProvider === 'ollama') {
      this.renderOllamaSettings(containerEl);
    } else {
      this.renderOpenAISettings(containerEl);
    }

    // ── Setup status ────────────────────────────────────────────────────
    containerEl.createEl('h3', { text: 'Setup' });

    new Setting(containerEl)
      .setName('Setup complete')
      .setDesc("Toggle off to see the 'Meet Dana' screen again on next panel open.")
      .addToggle(toggle =>
        toggle
          .setValue(this.plugin.settings.onboarded)
          .onChange(async value => {
            this.plugin.settings.onboarded = value;
            await this.plugin.saveSettings();
          })
      );
  }

  private renderOllamaSettings(containerEl: HTMLElement): void {
    new Setting(containerEl)
      .setName('Ollama host')
      .setDesc('Where Ollama is running.')
      .addText(text =>
        text
          .setPlaceholder('http://localhost:11434')
          .setValue(this.plugin.settings.ollamaHost)
          .onChange(async value => {
            this.plugin.settings.ollamaHost = value.trim();
            await this.plugin.saveSettings();
          })
      );

    new Setting(containerEl)
      .setName('Model')
      .setDesc('Which Ollama model to use. Try llama3.2, mistral, or phi3.')
      .addText(text =>
        text
          .setPlaceholder('llama3.2')
          .setValue(this.plugin.settings.ollamaModel)
          .onChange(async value => {
            this.plugin.settings.ollamaModel = value.trim();
            await this.plugin.saveSettings();
          })
      );

    new Setting(containerEl)
      .setName('Test connection')
      .setDesc('Verify Ollama is reachable.')
      .addButton(btn =>
        btn.setButtonText('Test').onClick(async () => {
          btn.setButtonText('Testing...').setDisabled(true);
          try {
            const resp = await fetch(`${this.plugin.settings.ollamaHost}/api/tags`);
            if (resp.ok) {
              const data = await resp.json();
              const models = data.models?.map((m: { name: string }) => m.name).join(', ') || 'none';
              new Notice(`Ollama is running. Models: ${models}`);
            } else {
              new Notice('Ollama responded with an error. Check the host URL.');
            }
          } catch {
            new Notice('Could not reach Ollama. Is it running?');
          }
          btn.setButtonText('Test').setDisabled(false);
        })
      );

    const hint = containerEl.createDiv('dana-settings-hint');
    hint.setText("Don't have Ollama? Install it free at ollama.com, then run: ollama pull llama3.2");
  }

  private renderOpenAISettings(containerEl: HTMLElement): void {
    const hasStoredKey = this.plugin.settings.openaiKeyEncrypted.length > 0;
    const isEncrypted = hasStoredKey
      ? this.plugin.settings.openaiKeyEncryptionAvailable
      : this.plugin.secretStore.isAvailable();

    new Setting(containerEl)
      .setName('OpenAI API key')
      .setDesc(
        isEncrypted
          ? 'Encrypted at rest using your OS keychain. Never stored in plain text.'
          : "OS-level encryption isn't available on this device, so this is stored as plain text in the plugin's data.json."
      )
      .addText(text => {
        text
          .setPlaceholder('sk-...')
          .setValue(this.plugin.getOpenAIKey())
          .onChange(async value => {
            this.plugin.setOpenAIKey(value.trim());
            await this.plugin.saveSettings();
            this.display();
          });
        text.inputEl.type = 'password';
      });
  }
}

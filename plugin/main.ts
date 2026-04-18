import { Plugin, WorkspaceLeaf } from 'obsidian';
import { DanaPanel, VIEW_TYPE_DANA } from './src/DanaPanel';
import { DanaSettings, DEFAULT_SETTINGS } from './src/types';
import { DanaSettingsTab } from './src/SettingsTab';

export default class DanaPlugin extends Plugin {
  settings: DanaSettings;

  async onload(): Promise<void> {
    await this.loadSettings();

    // Register sidebar panel view
    this.registerView(VIEW_TYPE_DANA, leaf => new DanaPanel(leaf, this));

    // Ribbon icon — leaf = nature, warm, not robot
    this.addRibbonIcon('leaf', 'Dana', () => this.activateView());

    // Command palette
    this.addCommand({
      id: 'dana-reflect-today',
      name: 'Reflect on today',
      callback: () => this.activateAndReflect(),
    });

    this.addCommand({
      id: 'dana-how-have-i-been',
      name: 'How have I been lately?',
      callback: () => this.activateAndReflect('How have I been lately?'),
    });

    this.addCommand({
      id: 'dana-open-panel',
      name: 'Open panel',
      callback: () => this.activateView(),
    });

    // Settings tab
    this.addSettingTab(new DanaSettingsTab(this.app, this));

    // Open panel on first run to show setup
    if (!this.settings.onboarded) {
      this.app.workspace.onLayoutReady(() => this.activateView());
    }
  }

  onunload(): void {
    this.app.workspace.detachLeavesOfType(VIEW_TYPE_DANA);
  }

  async activateView(): Promise<void> {
    const { workspace } = this.app;
    const existing = workspace.getLeavesOfType(VIEW_TYPE_DANA);

    if (existing.length > 0) {
      workspace.revealLeaf(existing[0]);
      return;
    }

    const leaf = workspace.getRightLeaf(false) as WorkspaceLeaf;
    await leaf.setViewState({ type: VIEW_TYPE_DANA, active: true });
    workspace.revealLeaf(leaf);
  }

  async activateAndReflect(prompt?: string): Promise<void> {
    await this.activateView();
    const leaves = this.app.workspace.getLeavesOfType(VIEW_TYPE_DANA);
    if (leaves.length > 0) {
      const panel = leaves[0].view as DanaPanel;
      await panel.reflect(prompt);
    }
  }

  async loadSettings(): Promise<void> {
    this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());
  }

  async saveSettings(): Promise<void> {
    await this.saveData(this.settings);
  }
}

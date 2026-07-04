import { Plugin, WorkspaceLeaf } from 'obsidian';
import { DanaPanel, VIEW_TYPE_DANA } from './src/DanaPanel';
import { DanaSettings, DEFAULT_SETTINGS } from './src/types';
import { DanaSettingsTab } from './src/SettingsTab';
import { JournalDetector } from './src/JournalDetector';

export default class DanaPlugin extends Plugin {
  settings: DanaSettings;
  journalDetector: JournalDetector;
  private ribbonIconEl: HTMLElement;

  async onload(): Promise<void> {
    await this.loadSettings();

    this.journalDetector = new JournalDetector();

    // Register sidebar panel view
    this.registerView(VIEW_TYPE_DANA, leaf => new DanaPanel(leaf, this));

    // Ribbon icon — leaf = nature, warm, not robot
    this.ribbonIconEl = this.addRibbonIcon('leaf', 'Dana', () => this.activateView());

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

    // Keep the ribbon icon dim when the active note isn't a journal entry
    this.registerEvent(this.app.workspace.on('active-leaf-change', () => this.updateRibbonState()));
    this.app.workspace.onLayoutReady(() => this.updateRibbonState());

    // Open panel on first run to show setup
    if (!this.settings.onboarded) {
      this.app.workspace.onLayoutReady(() => this.activateView());
    }
  }

  onunload(): void {
    this.app.workspace.detachLeavesOfType(VIEW_TYPE_DANA);
  }

  updateRibbonState(): void {
    const activeFile = this.app.workspace.getActiveFile();
    const frontmatter = activeFile
      ? this.app.metadataCache.getFileCache(activeFile)?.frontmatter ?? null
      : null;
    const isJournalNote = this.journalDetector.isJournalNote(
      activeFile,
      this.settings.journalFolder,
      frontmatter
    );
    this.ribbonIconEl.toggleClass('dana-ribbon-passive', !isJournalNote);
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

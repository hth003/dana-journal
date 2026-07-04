// Minimal Obsidian mock for unit tests of pure functions
export class Plugin {}
export class ItemView {}
export class Modal {}
export class PluginSettingTab {}
export class Setting {
  setName() { return this; }
  setDesc() { return this; }
  addText(cb: (t: any) => void) { cb({ setPlaceholder: () => ({ setValue: () => ({ onChange: () => ({}) }) }) }); return this; }
  addDropdown(cb: (d: any) => void) { cb({ addOption: () => ({ setValue: () => ({ onChange: () => ({}) }) }) }); return this; }
  addButton(cb: (b: any) => void) { cb({ setButtonText: () => ({ onClick: () => ({}) }) }); return this; }
  addToggle(cb: (t: any) => void) { cb({ setValue: () => ({ onChange: () => ({}) }) }); return this; }
}
export class Notice { constructor(_: string) {} }
export class TFile {}
export function setIcon() {}
export function parseYaml(s: string) { return {}; }

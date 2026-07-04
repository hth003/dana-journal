export interface SafeStorageLike {
  isEncryptionAvailable(): boolean;
  encryptString(plaintext: string): Buffer;
  decryptString(buffer: Buffer): string;
}

export class SecretStore {
  constructor(private safeStorage: SafeStorageLike | null) {}

  isAvailable(): boolean {
    if (!this.safeStorage) return false;
    try {
      return this.safeStorage.isEncryptionAvailable();
    } catch {
      return false;
    }
  }

  encrypt(plaintext: string): string | null {
    if (!plaintext || !this.isAvailable()) return null;
    try {
      return this.safeStorage!.encryptString(plaintext).toString('base64');
    } catch {
      return null;
    }
  }

  decrypt(ciphertext: string): string | null {
    if (!ciphertext || !this.safeStorage) return null;
    try {
      return this.safeStorage.decryptString(Buffer.from(ciphertext, 'base64'));
    } catch {
      return null;
    }
  }
}

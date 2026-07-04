import { SecretStore, SafeStorageLike } from '../src/SecretStore';

function makeFakeSafeStorage(overrides: Partial<SafeStorageLike> = {}): SafeStorageLike {
  return {
    isEncryptionAvailable: () => true,
    encryptString: (plaintext: string) => Buffer.from(`enc:${plaintext}`),
    decryptString: (buf: Buffer) => buf.toString('utf8').replace(/^enc:/, ''),
    ...overrides,
  };
}

describe('SecretStore', () => {
  it('reports availability from the underlying safeStorage', () => {
    const store = new SecretStore(makeFakeSafeStorage({ isEncryptionAvailable: () => true }));
    expect(store.isAvailable()).toBe(true);
  });

  it('reports unavailable when there is no safeStorage', () => {
    const store = new SecretStore(null);
    expect(store.isAvailable()).toBe(false);
  });

  it('round-trips encrypt and decrypt', () => {
    const store = new SecretStore(makeFakeSafeStorage());
    const ciphertext = store.encrypt('sk-test-123');
    expect(ciphertext).not.toBeNull();
    expect(ciphertext).not.toContain('sk-test-123');
    expect(store.decrypt(ciphertext!)).toBe('sk-test-123');
  });

  it('returns null from encrypt when encryption is unavailable', () => {
    const store = new SecretStore(makeFakeSafeStorage({ isEncryptionAvailable: () => false }));
    expect(store.encrypt('sk-test-123')).toBeNull();
  });

  it('returns null from encrypt when there is no safeStorage', () => {
    const store = new SecretStore(null);
    expect(store.encrypt('sk-test-123')).toBeNull();
  });

  it('returns null from decrypt when decryption throws', () => {
    const store = new SecretStore(
      makeFakeSafeStorage({
        decryptString: () => {
          throw new Error('bad ciphertext');
        },
      })
    );
    expect(store.decrypt('not-valid-base64!!')).toBeNull();
  });

  it('returns null from decrypt when there is no safeStorage', () => {
    const store = new SecretStore(null);
    expect(store.decrypt('anything')).toBeNull();
  });

  it('returns null from encrypt and decrypt for empty strings', () => {
    const store = new SecretStore(makeFakeSafeStorage());
    expect(store.encrypt('')).toBeNull();
    expect(store.decrypt('')).toBeNull();
  });
});

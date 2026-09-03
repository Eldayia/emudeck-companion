// A timeout ends UI waiting, not the underlying Decky RPC. Keep the gate closed
// until that RPC settles so polling cannot queue unlimited backend requests.
export function createSessionRead<T>(timeoutMs = 8000) {
  let pending = false;
  return (request: () => Promise<T>): Promise<T> | null => {
    if (pending) return null;
    pending = true;
    return new Promise<T>((resolve, reject) => {
      const timer = setTimeout(() => reject(new Error(
        "Emulator detection did not respond within 8 seconds. Restart Decky and check plugin_loader logs.",
      )), timeoutMs);
      // Promise callbacks receive a value, even undefined. Do not forward it
      // to Decky's variadic callable: Python expects zero RPC arguments here.
      Promise.resolve().then(() => request()).then(
        (value) => { pending = false; clearTimeout(timer); resolve(value); },
        (error) => { pending = false; clearTimeout(timer); reject(error); },
      );
    });
  };
}

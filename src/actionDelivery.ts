export async function deliverKeyboard(
  press: () => void | Promise<void>,
  report: (delivered: boolean, error: string) => Promise<{ ok: boolean }>,
): Promise<{ ok: boolean; error: string; reportError?: string }> {
  let error = "";
  let ok = true;
  try {
    await press();
  } catch (failure) {
    ok = false;
    error = String(failure);
  }
  // Never resend input if its diagnostic acknowledgement fails.
  try {
    if (!(await report(ok, error)).ok) return { ok, error, reportError: "Delivery report was not accepted" };
  } catch (failure) {
    return { ok, error, reportError: String(failure) };
  }
  return { ok, error };
}

export async function pressChord<T>(
  keys: T[], setState: (key: T, pressed: boolean) => void, wait: () => Promise<void>,
): Promise<void> {
  const attempted: T[] = [];
  let failed = false;
  let failure: unknown;
  try {
    for (const key of keys) {
      // A thrown API call may already have applied its state.
      attempted.push(key);
      setState(key, true);
    }
    await wait();
  } catch (error) {
    failed = true;
    failure = error;
  } finally {
    for (const key of attempted.reverse()) {
      try {
        setState(key, false);
      } catch (error) {
        if (!failed) { failed = true; failure = error; }
      }
    }
  }
  if (failed) throw failure;
}

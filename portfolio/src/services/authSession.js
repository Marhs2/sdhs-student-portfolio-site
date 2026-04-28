export const waitForSupabaseSession = (
  auth,
  { timeoutMs = 5000 } = {},
) =>
  new Promise((resolve, reject) => {
    let settled = false;
    let unsubscribe = null;
    const finish = (session) => {
      if (settled) {
        return;
      }
      settled = true;
      clearTimeout(timeoutId);
      unsubscribe?.();
      resolve(session || null);
    };
    const fail = (error) => {
      if (settled) {
        return;
      }
      settled = true;
      clearTimeout(timeoutId);
      unsubscribe?.();
      reject(error);
    };
    const timeoutId = setTimeout(() => finish(null), timeoutMs);

    const { data } = auth.onAuthStateChange((_event, session) => {
      if (session?.user) {
        finish(session);
      }
    });
    unsubscribe = () => data.subscription?.unsubscribe();

    auth
      .getSession()
      .then(({ data: sessionData, error }) => {
        if (error) {
          fail(error);
          return;
        }
        if (sessionData.session?.user) {
          finish(sessionData.session);
        }
      })
      .catch(fail);
  });

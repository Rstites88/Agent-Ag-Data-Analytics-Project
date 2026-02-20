interface Env {
  SESSION_STORE: KVNamespace;
  DB: D1Database;
  GOOGLE_CLIENT_ID: string;
  GOOGLE_CLIENT_SECRET: string;
  GOOGLE_REDIRECT_URI: string;
  ALLOWED_EMAILS: string;
}

interface GoogleUserInfo {
  id: string;
  email: string;
  name: string;
  picture: string;
}

interface SessionData {
  userId: string;
  email: string;
  name: string;
}

const SESSION_TTL = 86400; // 24 hours
const STATE_TTL = 600; // 10 minutes — CSRF state token lifetime
const MAX_AUTH_ATTEMPTS = 10; // per IP per window
const RATE_LIMIT_WINDOW = 300; // 5 minutes

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    if (request.method === 'OPTIONS') {
      return new Response(null, {
        headers: {
          'Access-Control-Allow-Origin': url.origin,
          'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
          'Access-Control-Allow-Headers': 'Content-Type',
        },
      });
    }

    try {
      switch (url.pathname) {
        case '/auth/google':
          return await handleLogin(request, env);
        case '/auth/callback':
          return await handleCallback(request, env);
        case '/auth/session':
          return await handleSessionCheck(request, env);
        case '/auth/logout':
          return await handleLogout(request, env);
        default:
          return new Response('Not Found', { status: 404 });
      }
    } catch {
      return new Response('Internal Server Error', { status: 500 });
    }
  },
};

async function checkRateLimit(request: Request, env: Env): Promise<boolean> {
  const ip =
    request.headers.get('CF-Connecting-IP') ||
    request.headers.get('X-Forwarded-For') ||
    'unknown';
  const key = `ratelimit:auth:${ip}`;
  const current = parseInt((await env.SESSION_STORE.get(key)) || '0', 10);

  if (current >= MAX_AUTH_ATTEMPTS) {
    return false;
  }

  await env.SESSION_STORE.put(key, String(current + 1), {
    expirationTtl: RATE_LIMIT_WINDOW,
  });
  return true;
}

async function handleLogin(request: Request, env: Env): Promise<Response> {
  const allowed = await checkRateLimit(request, env);
  if (!allowed) {
    return new Response('Too many requests. Try again later.', {
      status: 429,
      headers: { 'Retry-After': String(RATE_LIMIT_WINDOW) },
    });
  }

  const state = crypto.randomUUID();
  await env.SESSION_STORE.put(`oauth_state:${state}`, 'valid', {
    expirationTtl: STATE_TTL,
  });

  const authUrl = new URL('https://accounts.google.com/o/oauth2/v2/auth');
  authUrl.searchParams.set('client_id', env.GOOGLE_CLIENT_ID);
  authUrl.searchParams.set('redirect_uri', env.GOOGLE_REDIRECT_URI);
  authUrl.searchParams.set('response_type', 'code');
  authUrl.searchParams.set('scope', 'openid email profile');
  authUrl.searchParams.set('state', state);
  authUrl.searchParams.set('prompt', 'select_account');

  return Response.redirect(authUrl.toString(), 302);
}

async function handleCallback(request: Request, env: Env): Promise<Response> {
  const url = new URL(request.url);
  const code = url.searchParams.get('code');
  const state = url.searchParams.get('state');

  if (!code || !state) {
    return Response.redirect('/denied.html', 302);
  }

  const storedState = await env.SESSION_STORE.get(`oauth_state:${state}`);
  if (!storedState) {
    return Response.redirect('/denied.html', 302);
  }
  await env.SESSION_STORE.delete(`oauth_state:${state}`);

  const allowed = await checkRateLimit(request, env);
  if (!allowed) {
    return new Response('Too many requests. Try again later.', {
      status: 429,
      headers: { 'Retry-After': String(RATE_LIMIT_WINDOW) },
    });
  }

  const tokenResponse = await fetch('https://oauth2.googleapis.com/token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      code,
      client_id: env.GOOGLE_CLIENT_ID,
      client_secret: env.GOOGLE_CLIENT_SECRET,
      redirect_uri: env.GOOGLE_REDIRECT_URI,
      grant_type: 'authorization_code',
    }),
  });

  if (!tokenResponse.ok) {
    return Response.redirect('/denied.html', 302);
  }

  const tokens = (await tokenResponse.json()) as { access_token: string };

  const userInfoResponse = await fetch(
    'https://www.googleapis.com/oauth2/v2/userinfo',
    { headers: { Authorization: `Bearer ${tokens.access_token}` } }
  );

  if (!userInfoResponse.ok) {
    return Response.redirect('/denied.html', 302);
  }

  const userInfo: GoogleUserInfo = await userInfoResponse.json();

  const allowedEmails = env.ALLOWED_EMAILS.split(',').map((e) =>
    e.trim().toLowerCase()
  );

  if (!allowedEmails.includes(userInfo.email.toLowerCase())) {
    return Response.redirect('/denied.html', 302);
  }

  await env.DB.prepare(
    `INSERT INTO users (id, email, name, picture_url, updated_at)
     VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
     ON CONFLICT(id) DO UPDATE SET
       name = excluded.name,
       picture_url = excluded.picture_url,
       updated_at = CURRENT_TIMESTAMP`
  )
    .bind(userInfo.id, userInfo.email, userInfo.name, userInfo.picture)
    .run();

  const sessionToken = crypto.randomUUID();
  const sessionData: SessionData = {
    userId: userInfo.id,
    email: userInfo.email,
    name: userInfo.name,
  };

  await env.SESSION_STORE.put(
    `session:${sessionToken}`,
    JSON.stringify(sessionData),
    { expirationTtl: SESSION_TTL }
  );

  return new Response(null, {
    status: 302,
    headers: {
      Location: '/dashboard.html',
      'Set-Cookie': `session=${sessionToken}; HttpOnly; Secure; SameSite=Lax; Max-Age=${SESSION_TTL}; Path=/`,
    },
  });
}

async function handleSessionCheck(
  request: Request,
  env: Env
): Promise<Response> {
  const sessionToken = extractSessionToken(request);

  if (!sessionToken) {
    return Response.json({ authenticated: false }, { status: 401 });
  }

  const sessionRaw = await env.SESSION_STORE.get(`session:${sessionToken}`);
  if (!sessionRaw) {
    return Response.json({ authenticated: false }, { status: 401 });
  }

  const session: SessionData = JSON.parse(sessionRaw);
  return Response.json({
    authenticated: true,
    email: session.email,
    name: session.name,
  });
}

async function handleLogout(request: Request, env: Env): Promise<Response> {
  const sessionToken = extractSessionToken(request);

  if (sessionToken) {
    await env.SESSION_STORE.delete(`session:${sessionToken}`);
  }

  return new Response(null, {
    status: 302,
    headers: {
      Location: '/',
      'Set-Cookie':
        'session=; HttpOnly; Secure; SameSite=Lax; Max-Age=0; Path=/',
    },
  });
}

function extractSessionToken(request: Request): string | undefined {
  const cookie = request.headers.get('Cookie') || '';
  return cookie
    .split(';')
    .find((c) => c.trim().startsWith('session='))
    ?.split('=')[1]
    ?.trim();
}

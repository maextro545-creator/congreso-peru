const fs = require('fs');
const path = require('path');
const https = require('https');

// Helper to make https requests
function request(options, body) {
  return new Promise((resolve, reject) => {
    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => data += chunk);
      res.on('end', () => resolve({ statusCode: res.statusCode, body: data }));
    });
    req.on('error', reject);
    if (body) req.write(JSON.stringify(body));
    req.end();
  });
}

module.exports = async (req, res) => {
  // Allow CORS
  res.setHeader('Access-Control-Allow-Credentials', true);
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET,OPTIONS,PATCH,DELETE,POST,PUT');
  res.setHeader('Access-Control-Allow-Headers', 'X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version, Authorization');

  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  if (req.method !== 'POST') {
    res.status(405).json({ error: 'Method not allowed' });
    return;
  }

  const { username, password, data } = req.body;

  if (username !== 'KEVIN' || password !== '987077308') {
    res.status(401).json({ error: 'Credenciales incorrectas' });
    return;
  }

  if (!data) {
    res.status(400).json({ error: 'Falta el contenido del JSON' });
    return;
  }

  // Local dev mode
  if (process.env.NODE_ENV !== 'production') {
    try {
      const filePath = path.join(process.cwd(), 'data.json');
      fs.writeFileSync(filePath, JSON.stringify(data, null, 2), 'utf8');
      res.status(200).json({ message: 'Guardado localmente con éxito' });
      return;
    } catch (err) {
      res.status(500).json({ error: 'Error al escribir data.json localmente: ' + err.message });
      return;
    }
  }

  // Production Vercel mode: commit to GitHub
  const token = process.env.GITHUB_TOKEN;
  if (!token) {
    res.status(500).json({ 
      error: 'Falta configurar GITHUB_TOKEN en las variables de entorno de Vercel.',
      setupHelp: true 
    });
    return;
  }

  // Get repo details from Vercel env or fallback
  const owner = process.env.VERCEL_GIT_REPO_OWNER || 'maextro545-creator';
  const repo = process.env.VERCEL_GIT_REPO_SLUG || 'congreso-peru';
  const branch = process.env.VERCEL_GIT_COMMIT_REF || 'master';
  const filePath = 'data.json';

  try {
    // 1. Get SHA of current data.json
    const getOptions = {
      hostname: 'api.github.com',
      path: `/repos/${owner}/${repo}/contents/${filePath}?ref=${branch}`,
      method: 'GET',
      headers: {
        'User-Agent': 'Vercel-Serverless-Function',
        'Authorization': `token ${token}`,
        'Accept': 'application/vnd.github.v3+json'
      }
    };

    const getRes = await request(getOptions);
    if (getRes.statusCode !== 200) {
      res.status(getRes.statusCode).json({ error: `Error al obtener SHA de GitHub: ${getRes.body}` });
      return;
    }

    const fileInfo = JSON.parse(getRes.body);
    const sha = fileInfo.sha;

    // 2. Put new content (base64 encoded)
    const newContentBase64 = Buffer.from(JSON.stringify(data, null, 2)).toString('base64');
    
    const putOptions = {
      hostname: 'api.github.com',
      path: `/repos/${owner}/${repo}/contents/${filePath}`,
      method: 'PUT',
      headers: {
        'User-Agent': 'Vercel-Serverless-Function',
        'Authorization': `token ${token}`,
        'Accept': 'application/vnd.github.v3+json',
        'Content-Type': 'application/json'
      }
    };

    const putBody = {
      message: 'Dashboard-update: Modificación de diseño o puntuación del Congreso',
      content: newContentBase64,
      sha: sha,
      branch: branch
    };

    const putRes = await request(putOptions, putBody);
    if (putRes.statusCode === 200 || putRes.statusCode === 201) {
      res.status(200).json({ 
        message: '¡Cambios guardados con éxito en GitHub! Vercel está reconstruyendo la web (tardará unos 20-30 segundos en reflejarse).' 
      });
    } else {
      res.status(putRes.statusCode).json({ error: `Error al subir a GitHub: ${putRes.body}` });
    }
  } catch (err) {
    res.status(500).json({ error: 'Excepción en la API de guardado: ' + err.message });
  }
};

# SymptoCare - Vercel Deployment Guide (Frontend + Backend)

## 🎯 Deployment Overview

- **Frontend**: Static files (HTML/CSS/JS) deployed on Vercel CDN
- **Backend**: FastAPI serverless functions on Vercel
- **API**: All backend routes accessible via `/api/*`

---

## Step-by-Step Deployment Instructions

### **Step 1: Prepare Your Repository**

1. Initialize Git (if not already done):
```bash
git init
git add .
git commit -m "Initial commit - ready for Vercel deployment"
```

2. Push to GitHub:
```bash
git remote add origin https://github.com/YOUR_USERNAME/SymptoCare.git
git branch -M main
git push -u origin main
```

---

### **Step 2: Setup Vercel Account**

1. Go to [vercel.com](https://vercel.com)
2. Click **"Sign Up"** → **"Continue with GitHub"**
3. Authorize Vercel to access your GitHub repositories
4. You'll be redirected to Vercel dashboard

---

### **Step 3: Create Vercel Account & Connect Repository**

1. Go to [vercel.com](https://vercel.com)
2. Click **"Sign Up"** or **"Log In"**
3. Choose **"Continue with GitHub"** (or GitLab/Bitbucket)
4. Authorize Vercel to access your repositories
5. Click **"Import Project"**
6. Select yourImport Project**

1. In Vercel dashboard, click **"Add New"** → **"Project"**
2. Click **"Import Git Repository"**
3. Search for **"SymptoCProject Settings**

On the **"Configure your Project"** page:

| Setting | Value |
|---------|-------|
| **Framework** | Other |
| **Build Command** | `npm run build` |
| **Output Directory** | `frontend` |
| **Install Command** | `pip install -r**

Before deploying, click **"Environment Variables"**:

Add these variables (available in all environments):

| Variable | Value | Example |
|----------|-------|---------|
| `SUPABASE_URL` | Your Supabase project URL | `https://abc123.supabase.co` |
| `SUPABASE_ANON_KEY` | Your Supabase anonymous key | `eyJ0eXAi...` |
| `CORS_ORIGINS` | Frontend URL | `https://your-domain.vercel.app` |

✅ Make sure to select **Production, Preview, Development** for each variable | Your Supabase URL |
   | `SUPABASE_ANON_KEY` | Your Supabase Anon Key |
   | `CORS_ORIGINS` | `http://localhost:3000,https://your-domain.vercel.app` |

3. Selectthe **"Deploy"** button
2. Vercel will:
   - Build the frontend
   - Install Python dependencies
   - Deploy API functions
   - Setup serverless backend
3. Wait 3-5 minutes for deployment to complete
4. You'll get a URL: **`https://your-domain.vercel.app`** ✅
---
Open in browser: `https://your-domain.vercel.app`

You should see your app's homepage.

#### **Test Backend API:**

**Health Check:**
```bash
curl https://your-domain.vercel.app/api/health
```

Expected response:
```json
{"status":"healthy","service":"SymptoCare API"}
```

**Test Prediction Endpoint:**Configuration**

Update your `frontend/config.js` (or where API URL is defined):

```javascript
// OLD - Local development
const API_BASE_URL = 'http://localhost:8000';

// NEW - After Vercel deployment
const API_BASE_URL = 'https://your-domain.vercel.app/api';
```

Then update any API calls in your JavaScript:

```javascript
// Example API call
fetch(`${API_BASE_URL}/predict`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ symptoms: ['fever', 'cough'] })
});
```

Push ✅ Project Structure**

```
SymptoCare/
├── vercel.json              ← Vercel configuration
├── package.json             ← Build config
├── requirements.txt         ← Python dependencies
├── .vercelignore            ← Files to exclude
├── .env.example             ← Env template
├── api/
│   └── index.py            ← Backend API (serverless)
├── frontend/                ← Frontend (static)
│   ├── index.html
│   ├── app.html
│   ├── login.html
│   ├── signup.html
│   ├── config.js            ← UPDATE API URL HERE!
│   ├── app.js
│   ├── auth.js
│   └── styles.css
└── backend/
    ├── app.py               ← Local development onl)
const API_BASE_URL = 'http://localhost:8000';

// NEW (Vercel)
const API_BASE_URL = 'https://your-domain.vercel.app/api';
```
🔧 Troubleshooting**

### **Build Fails During Deployment**
**Solution:**
- Check Vercel logs: Dashboard → Your Project → Deployments → Click failed build
- Ensure `requirements.txt` has all Python packages
- Run locally first: `python -m uvicorn api.index:app`

### **API Returns 500 Error**
**Solution:**
- Verify environment variables are set in Vercel dashboard
- Check function logs: Dashboard → Logs
- Test endpoint with curl to see error details

### **CORS Errors (Frontend can't call API)**
**Solution:**
- Update `CORS_ORIGINS` in environment variables to include your Vercel domain
- Example: `https://your-domain.vercel.app`
- Redeploy after updating

### **Frontend Not Loading**
**Solution:**
- Ensure all HTML/CSS/JS files are in `frontend/` folder
- Che📌 Important Notes**

✅ **Frontend** = Static files served from `/frontend` directory

✅ **Backend** = Serverless Python functions at `/api/*`

✅ **All API routes** must include `/api/` prefix
   - `POST /api/predict` ✅
   - `POST /api/auth/login` ✅
   - `GET /api/health` ✅

✅ **Environment variables** are encrypted and secure

✅ **Free tier includes:**
   - Unlimited deployments
   - 100GB bandwidth/month
   - 🔄 Redeploy After Changes**

Simply push to GitHub:
```bash
git add .
git commit -m "Fix API endpoints"
git push origin main
```

Vercel automatically rebuilds and redeploys! No manual steps needed. ✨

---

## **📊 Monitoring & Logs**

View live logs in Vercel Dashboard:
1. Go to your project
2. Click **"Logs"** tab
3. Filter by **Deployment**, **Function**, or **Edge**

Check deployment status:
1. Click **"Deployments"** tab
2. See all builds with status (Success/Failed)
3. Click build to see detailed logs

---

## **🌐 Custom Domain (Optional)**

1. In Vercel Dashboard → **Settings** → **Domains**
2. Add your domain (e.g., `symptocare.com`)
3. Update DNS records (Vercel provides instructions)
4. Update `CORS_ORIGINS` environment variable:
   ```
   https://symptocare.com
   ```
5. Redeploy

---

## **✨ You're Done!**

Your SymptoCare app is now live! 🚀

- **Frontend:** `https://your-domain.vercel.app`
- **Backend API:** `https://your-domain.vercel.app/api/*`
- **Dashboard:** Vercel analytics and logs

For questions, check [Vercel docs](https://vercel.com/docs)
- Verify environment variables are set

### **Issue: API Returns 500 Error**
- Check environment variables (SUPABASE_URL, SUPABASE_ANON_KEY)
- Review function logs in Vercel Dashboard
- Test locally first with `python -m uvicorn api.index:app`

### **Issue: CORS Errors**
- Update `CORS_ORIGINS` in environment variables
- Include your Vercel domain

### **Issue: Frontend Not Loading**
- Ensure all static files are in the `frontend/` directory
- Check that HTML paths don't start with `/`
- Verify CSS/JS file references are relative paths

---

## **Important Notes**

✅ **Frontend** is deployed as static files from `/frontend` directory

✅ **Backend** is deployed as serverless function at `/api/*`

✅ API calls should use `https://your-domain.vercel.app/api/*`

✅ Environment variables are encrypted and secure

✅ Free tier includes 100GB bandwidth/month

✅ Cold starts on first request (normal for serverless)

---

## **Redeploy After Changes**

Simply push to your repository:
```bash
git add .
git commit -m "Update changes"
git push origin main
```

Vercel automatically rebuilds and deploys! 🚀

---

## **Custom Domain (Optional)**

1. In Vercel Dashboard → **Settings** → **Domains**
2. Add your custom domain
3. Update DNS records (instructions provided by Vercel)
4. Update `CORS_ORIGINS` environment variable with new domain

---

Good luck! Your SymptoCare app will be live on Vercel! 🎉

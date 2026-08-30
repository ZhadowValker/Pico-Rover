# GitHub Pages Deployment Guide

## Overview

The Pico Rover web frontend is deployed automatically to GitHub Pages, making it accessible at:

```
https://zhadowvalker.github.io/Pico-Rover/
```

This guide covers enabling GitHub Pages and troubleshooting deployment issues.

---

## ✅ Quick Setup (5 minutes)

### Step 1: Enable GitHub Pages

1. Go to your repository: https://github.com/ZhadowValker/Pico-Rover
2. Click **Settings** (top right)
3. Click **Pages** (left sidebar)
4. Under "Build and deployment":
   - **Source:** Select "Deploy from a branch"
   - **Branch:** Select `main`
   - **Folder:** Select `/frontend`
   - Click **Save**

### Step 2: Verify Deployment

1. Wait 1-2 minutes for build to complete
2. Go to **Actions** tab
3. Look for recent workflow run with green checkmark ✓
4. Visit https://zhadowvalker.github.io/Pico-Rover/ in browser

You should see the Pico Rover control interface!

---

## 🔧 Troubleshooting

### Issue: "404 Not Found" at GitHub Pages URL

**Symptom:** GitHub Pages URL exists but returns 404

**Solutions:**

1. **Check Pages is enabled:**
   - Settings → Pages
   - Verify "Deploy from a branch" is selected
   - Verify branch = `main`, folder = `/frontend`

2. **Check /frontend folder exists:**
   ```bash
   cd /home/claude/Pico-Rover
   ls -la frontend/
   # Should show: index.html, css/, js/, libs/
   ```

3. **Check index.html in frontend:**
   ```bash
   [ -f frontend/index.html ] && echo "✓ index.html found" || echo "✗ Missing"
   ```

4. **Wait for deployment:**
   - GitHub Actions take 1-2 minutes
   - Check **Actions** tab for build status
   - Green checkmark ✓ = deployed successfully

### Issue: Assets (CSS/JS) Not Loading

**Symptom:** Page loads but CSS is missing, no styling

**Causes & Solutions:**

1. **Check asset paths in index.html:**
   ```html
   <!-- CORRECT -->
   <link rel="stylesheet" href="/Pico-Rover/css/style.css">
   <script src="/Pico-Rover/js/app.js"></script>
   
   <!-- WRONG (missing /Pico-Rover) -->
   <link rel="stylesheet" href="/css/style.css">
   ```

2. **Browser cache issue:**
   - Hard refresh: `Ctrl+Shift+R` (or `Cmd+Shift+R` on Mac)
   - Clear cookies/cache for the domain
   - Try incognito window

3. **Check file structure:**
   ```bash
   tree frontend/
   ```
   
   Expected:
   ```
   frontend/
   ├── index.html
   ├── css/
   │   └── style.css
   ├── js/
   │   ├── app.js
   │   ├── api.js
   │   ├── control.js
   │   ├── gyro.js
   │   ├── joystick.js
   │   └── ui.js
   └── libs/
       └── nipple.js
   ```

### Issue: Rover Cannot Connect to Frontend

**Symptom:** Frontend loads but shows "No rover found" or "Connection failed"

**This is expected!** The frontend and Pico need to be on the same WiFi network.

**Solution:**
1. Connect phone/computer to Pico's WiFi AP first:
   - SSID: "RoverSetup"
   - Password: "rover1234"
   - IP: http://192.168.4.1

2. Once Pico is on home WiFi:
   - Open https://zhadowvalker.github.io/Pico-Rover/
   - Frontend auto-discovers Pico on LAN
   - Click "Connect" when found

---

## 📋 Deployment Checklist

Before considering GitHub Pages working, verify:

- [ ] Settings → Pages enabled (Deploy from branch)
- [ ] Branch set to `main`
- [ ] Folder set to `/frontend`
- [ ] Save button clicked
- [ ] Wait 1-2 minutes for build
- [ ] Actions tab shows green checkmark ✓
- [ ] Visit GitHub Pages URL in browser
- [ ] Page loads (HTML + content visible)
- [ ] CSS loads (page has styling, not plain HTML)
- [ ] JavaScript loads (console has no errors)
- [ ] Hard refresh doesn't show errors

---

## 🔄 Continuous Deployment

### How It Works

Every time you push to `main` branch:

1. **GitHub Actions triggers** (automatic)
   - Runs linting checks
   - Validates file structure
   - Generates build report

2. **GitHub Pages auto-deploys** (automatic)
   - Copies `/frontend` folder to GitHub Pages
   - Rebuilds site
   - Available at your GitHub Pages URL

3. **Takes ~1-2 minutes**
   - Check Actions tab for status
   - Green checkmark = deployed
   - Red X = check logs for errors

### Workflow Files

Located at `.github/workflows/ci.yml`:

- **Triggers:** On push to `main` or pull requests
- **Jobs:**
  - Python linting (firmware code)
  - JavaScript linting (frontend code)
  - JSON validation
  - Markdown linting
  - File structure validation
  - Build status report
  - Pages config check

### Viewing Build Logs

1. Go to **Actions** tab in your repo
2. Click latest workflow run
3. Expand job sections to see details
4. Check for ✓ (passed) or ✗ (failed)

---

## 🌐 Custom Domain (Optional)

If you want to use a custom domain (e.g., `rover.example.com`):

1. Get a domain name (GoDaddy, Namecheap, etc.)
2. Settings → Pages → Custom domain
3. Enter your domain
4. Update DNS records (see GitHub's instructions)
5. Enable HTTPS (GitHub auto-provisions SSL cert)

---

## 🚀 Manual Force Deployment

If GitHub Pages doesn't deploy automatically:

1. Go to **Settings → Pages**
2. Change "Source" to "Workflow"
3. Select "Deploy from a branch" workflow
4. Click **Save**
5. Go to **Actions** tab
6. Find "pages build and deployment" workflow
7. Click **Run workflow**
8. Wait 1-2 minutes

---

## 📊 Monitoring Deployment

### Health Check Script

Save as `scripts/health-check.sh`:

```bash
#!/bin/bash

REPO="ZhadowValker/Pico-Rover"
PAGES_URL="https://zhadowvalker.github.io/Pico-Rover/"

echo "🔍 GitHub Pages Health Check"
echo ""

# Check if pages URL is reachable
echo "Testing: $PAGES_URL"
status=$(curl -o /dev/null -s -w "%{http_code}" "$PAGES_URL")

if [ "$status" = "200" ]; then
    echo "✓ Pages site is live (HTTP $status)"
else
    echo "✗ Pages site unreachable (HTTP $status)"
    exit 1
fi

# Check if index.html loads
echo ""
echo "Testing: index.html"
curl -s "$PAGES_URL" | grep -q "<title>" && \
    echo "✓ index.html loaded" || \
    echo "✗ index.html missing"

# Check if CSS loads
echo ""
echo "Testing: CSS assets"
curl -s "$PAGES_URL" | grep -q "style.css" && \
    echo "✓ CSS references found" || \
    echo "✗ CSS missing"

# Check if JS loads
echo ""
echo "Testing: JavaScript assets"
curl -s "$PAGES_URL" | grep -q "app.js" && \
    echo "✓ JS references found" || \
    echo "✗ JS missing"

echo ""
echo "✅ All checks passed!"
```

Run with:
```bash
chmod +x scripts/health-check.sh
./scripts/health-check.sh
```

---

## 🛠️ Common Configuration Issues

### Issue: "GitHub Pages not enabled"

Error: "Ensure GitHub Pages has been enabled"

**Solution:**
- Settings → Pages → Source: "Deploy from a branch"
- Save changes
- Wait 1-2 minutes

### Issue: "Custom domain not working"

**Solution:**
- Verify DNS records are correct
- Check custom domain in Settings → Pages
- Wait up to 24 hours for DNS propagation
- Clear browser cache

### Issue: "Workflow failures"

**Solution:**
- Check Actions tab for error logs
- Common issues:
  - File permissions (missing executable bit)
  - Asset path issues (hardcoded `/` instead of `/Pico-Rover/`)
  - Missing files in commit

---

## 📚 Related Documentation

- [GitHub Pages Official Docs](https://docs.github.com/en/pages)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [ARCHITECTURE.md](./ARCHITECTURE.md) - System architecture
- [CUSTOMIZATION.md](./CUSTOMIZATION.md) - Frontend customization

---

## 🎯 Next Steps After Enabling Pages

1. **Visit your live site:** https://zhadowvalker.github.io/Pico-Rover/
2. **Connect Pico W to home WiFi** (see SETUP.md)
3. **Test rover control:**
   - Open Pages URL on mobile
   - Request gyro permission
   - Tilt phone to drive rover 🎮
4. **Monitor CI/CD:** Check Actions tab for build status
5. **Iterate:** Push code → auto-deploys to Pages

---

## ❓ FAQ

**Q: How long does deployment take?**
A: Usually 1-2 minutes from push to live

**Q: Can I disable auto-deployment?**
A: Yes, Settings → Pages → change Source to "Workflow" (manual)

**Q: What if I only want `/frontend` deployed?**
A: That's already configured! Only `/frontend` folder goes to Pages

**Q: Can I use a different branch?**
A: Yes, Settings → Pages → change Branch (but use `main` for simplicity)

**Q: What if I accidentally push bad code?**
A: Just push again with fixes, Pages will re-deploy

**Q: Is the frontend automatically updated?**
A: Yes! Every push to `main` auto-deploys within 1-2 minutes

---

## ✅ GitHub Actions Updates

The CI/CD workflow has been updated to:

- ✅ **Node 20** (Node 24 compatible, no deprecation warnings)
- ✅ **Automatic linting** on every push
- ✅ **Build status reports** in Actions summary
- ✅ **Pages config verification** (no more deployment errors)
- ✅ **Simplified deployment** (rely on GitHub Pages auto-deploy)

---

**Status:** ✅ GitHub Pages ready to deploy

**To enable:** Follow the **Quick Setup** section above (5 minutes)

**Dashboard:** https://github.com/ZhadowValker/Pico-Rover/actions (monitor builds)

**Live Site:** https://zhadowvalker.github.io/Pico-Rover/ (after enabling)

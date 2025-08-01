# 🚀 PythonAnywhere Deployment Guide

## Step-by-Step Deployment Instructions

### **Step 1: Create PythonAnywhere Account**
1. Go to [pythonanywhere.com](https://pythonanywhere.com)
2. Click **"Create a Beginner account"** (free tier)
3. Complete registration with your email

### **Step 2: Upload Your Files**
1. **Log in** to PythonAnywhere dashboard
2. Go to **"Files"** tab
3. **Create directory**: `budget-planner`
4. **Upload all files** from your local project:
   - `app.py`
   - `requirements.txt`
   - `templates/` folder
   - `static/` folder
   - `pythonanywhere_wsgi.py`

### **Step 3: Set Up Python Environment**
1. Go to **"Consoles"** tab
2. Start a **Bash console**
3. Navigate to your project:
   ```bash
   cd budget-planner
   ```
4. Install dependencies:
   ```bash
   pip3 install --user flask
   ```

### **Step 4: Configure Web App**
1. Go to **"Web"** tab
2. Click **"Add a new web app"**
3. Choose **"Flask"** and **Python 3.9**
4. Set **Source code**: `/home/YOUR_USERNAME/budget-planner`
5. Set **Working directory**: `/home/YOUR_USERNAME/budget-planner`

### **Step 5: Configure WSGI File**
1. Click on your web app
2. Go to **"Code"** section
3. Click **"WSGI configuration file"**
4. Replace the content with the content from `pythonanywhere_wsgi.py`
5. **Update the username** in the path: `/home/YOUR_USERNAME/budget-planner`
6. Save the file

### **Step 6: Set Environment Variables**
In the WSGI file, make sure these are set:
```python
os.environ['SECRET_KEY'] = '7b1eeabcd208616a73edadcc5b91e9dd56503f2487d9077e22d81ba84ccb1c43'
os.environ['DATABASE_PATH'] = '/home/YOUR_USERNAME/budget-planner/data'
```

### **Step 7: Reload Web App**
1. Go back to **"Web"** tab
2. Click **"Reload"** button
3. Wait for the green checkmark

## ✅ **Benefits of PythonAnywhere:**

### **Persistent Storage:**
- ✅ **Database files persist** between deployments
- ✅ **User data is safe** and won't be lost
- ✅ **File storage** is permanent

### **Free Tier Features:**
- ✅ **512 MB storage** (enough for your app)
- ✅ **1 web app** (perfect for your budget planner)
- ✅ **Unlimited CPU time** for web apps
- ✅ **Custom domains** supported

### **Easy Management:**
- ✅ **Web-based file editor**
- ✅ **Console access** for debugging
- ✅ **Log viewing** for troubleshooting
- ✅ **One-click reloads**

## 🔧 **Troubleshooting:**

### **Common Issues:**
1. **Import errors**: Check that all files are uploaded
2. **Database errors**: Ensure `data/` directory exists
3. **500 errors**: Check WSGI configuration
4. **404 errors**: Verify web app configuration

### **Debugging:**
1. **Check error logs** in Web tab
2. **Use console** for testing
3. **Verify file paths** in WSGI file
4. **Test locally** before uploading

## 🎯 **Your App URL:**
Once deployed, your app will be available at:
`https://YOUR_USERNAME.pythonanywhere.com`

## 📱 **Mobile Testing:**
- Test on your phone
- Check responsive design
- Verify all features work

Your data will now persist between deployments! 🎉 
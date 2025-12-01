# 🎥 How to Make Videos Play on GitHub README

GitHub doesn't directly support embedded MP4 videos in README files, but there are several methods to make videos playable:

## ✅ Method 1: Upload to GitHub Assets (Recommended)

This creates a native GitHub video player in your README.

### Steps:

1. **Create a Draft Release** (or use an existing issue/PR):
   ```bash
   # Go to your GitHub repository
   # Navigate to: Issues → New Issue
   ```

2. **Upload Videos**:
   - Drag and drop your MP4 files into the issue comment box
   - GitHub will upload them and generate URLs like:
     ```
     https://github.com/user-attachments/assets/VIDEO_ID_HERE
     ```
   - **Copy these URLs** (don't submit the issue, just close it)

3. **Update README.md**:
   Replace the placeholder URLs in README.md:
   ```markdown
   ### 🕵️ Exploratory Agent in Action
   
   https://github.com/user-attachments/assets/YOUR_ACTUAL_VIDEO_ID
   ```

4. **Commit and Push**:
   ```bash
   git add README.MD
   git commit -m "docs: add playable demo videos"
   git push origin main
   ```

### Result:
✅ Videos play directly in GitHub with a native player
✅ No external hosting needed
✅ Works on mobile and desktop

---

## 🎬 Method 2: Convert to GIF (For Quick Previews)

If videos are too large or you want instant inline playback:

### Steps:

1. **Convert MP4 to GIF**:
   ```bash
   # Install ffmpeg if needed
   brew install ffmpeg
   
   # Convert video (adjust quality/size as needed)
   ffmpeg -i "demo/Exploratory Steps.mp4" \
          -vf "fps=10,scale=800:-1:flags=lanczos" \
          -loop 0 \
          demo/exploratory_steps.gif
   
   ffmpeg -i "demo/Execution of Generated Test Steps.mp4" \
          -vf "fps=10,scale=800:-1:flags=lanczos" \
          -loop 0 \
          demo/test_execution.gif
   ```

2. **Update README.md**:
   ```markdown
   ### 🕵️ Exploratory Agent in Action
   
   ![Exploratory Demo](demo/exploratory_steps.gif)
   
   ### ✅ Automated Test Execution
   
   ![Test Execution](demo/test_execution.gif)
   ```

3. **Commit GIFs**:
   ```bash
   git add demo/*.gif README.MD
   git commit -m "docs: add demo GIFs"
   git push
   ```

### Result:
✅ Plays automatically (no click needed)
✅ Inline in README
❌ Lower quality than video
❌ Larger file size for long videos

---

## 📦 Method 3: Use GitHub Releases

Upload videos to a GitHub Release for permanent hosting:

### Steps:

1. **Create a Release**:
   ```bash
   # Via GitHub UI:
   # Go to: Releases → Draft a new release
   # Tag: v1.0.0
   # Title: Initial Release
   ```

2. **Attach Videos**:
   - Drag MP4 files to the release assets section
   - Publish the release

3. **Link in README**:
   ```markdown
   ### 🎥 Demo Videos
   
   - [📹 Exploratory Agent](https://github.com/username/repo/releases/download/v1.0.0/Exploratory_Steps.mp4)
   - [📹 Test Execution](https://github.com/username/repo/releases/download/v1.0.0/Test_Execution.mp4)
   ```

### Result:
✅ Permanent links
✅ Versioned assets
❌ Requires download (no inline player)

---

## 🌐 Method 4: External Hosting (YouTube, Vimeo)

For professional demos or large files:

### Steps:

1. **Upload to YouTube**:
   - Go to [YouTube Studio](https://studio.youtube.com/)
   - Upload videos as unlisted
   - Copy video ID from URL: `youtube.com/watch?v=VIDEO_ID`

2. **Embed in README**:
   ```markdown
   ### 🕵️ Exploratory Agent in Action
   
   [![Watch Demo](https://img.youtube.com/vi/VIDEO_ID/maxresdefault.jpg)](https://www.youtube.com/watch?v=VIDEO_ID)
   ```

### Result:
✅ High quality streaming
✅ Analytics available
✅ Thumbnail preview in README
❌ Requires external platform
❌ Can't be private repository

---

## 🎯 Recommended Approach for This Project

**Use Method 1 (GitHub Assets)** for the best user experience:

1. Upload both videos via GitHub issue upload
2. Get the `user-attachments/assets/` URLs
3. Replace placeholders in README.md
4. Keep original MP4 files in `demo/` folder as backup

This provides:
- ✅ Native GitHub player
- ✅ No external dependencies
- ✅ Fast loading
- ✅ Professional appearance

---

## 📏 Video Optimization Tips

Before uploading, optimize videos for web:

```bash
# Reduce file size while maintaining quality
ffmpeg -i input.mp4 \
       -vcodec libx264 \
       -crf 28 \
       -preset slow \
       -vf "scale=1280:-2" \
       output_optimized.mp4

# Target: < 10MB per video for fast GitHub loading
```

---

## ✅ Final Checklist

- [ ] Videos are < 10MB each (GitHub recommendation)
- [ ] Videos are in MP4 format (H.264 codec)
- [ ] Uploaded to GitHub via issue/PR comment
- [ ] URLs copied and pasted into README.md
- [ ] README.md committed and pushed
- [ ] Verified videos play on GitHub web interface
- [ ] Original MP4 files kept in `demo/` folder

---

**Need Help?** Check [GitHub's documentation on video uploads](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/attaching-files)

# 📋 Manual Testing Checklist for Cropio

## 🎯 **COMPREHENSIVE MANUAL TESTING GUIDE**

This checklist provides step-by-step manual testing procedures to verify all aspects of your Cropio converter platform. Follow each section systematically to ensure production readiness.

---

## ✅ **PRE-TESTING SETUP**

### Prerequisites Checklist:
- [ ] Application running at `http://localhost:5000`
- [ ] Database is running and accessible
- [ ] All test files prepared (see Test Files section)
- [ ] Browser with developer tools ready
- [ ] Network tools available (optional)

### Start Application:
```bash
.\\venv\\Scripts\\python.exe app.py
```

---

## 🧪 **CATEGORY 1: USER AUTHENTICATION & SECURITY**

### 1.1 User Registration
- [ ] **Navigate to registration page** (`/auth/register`)
- [ ] **Test valid registration**:
  - [ ] Fill form with valid data
  - [ ] Submit form
  - [ ] Verify success message
  - [ ] Check user redirected appropriately
- [ ] **Test invalid inputs**:
  - [ ] Invalid email format → Error message shown
  - [ ] Weak password → Error message shown  
  - [ ] Duplicate email → Error message shown
  - [ ] Missing required fields → Error messages shown
- [ ] **Test email verification** (if configured):
  - [ ] Registration triggers email
  - [ ] Email contains verification link
  - [ ] Clicking link activates account

**Expected Results**: ✅ Registration works with proper validation

### 1.2 User Login
- [ ] **Navigate to login page** (`/auth/login`)
- [ ] **Test valid login**:
  - [ ] Enter correct credentials
  - [ ] Submit form
  - [ ] Verify redirect to dashboard/home
  - [ ] Check user session established
- [ ] **Test invalid login**:
  - [ ] Wrong password → Error message
  - [ ] Non-existent email → Error message
  - [ ] Empty fields → Validation errors
- [ ] **Test "Remember Me"** (if available)
- [ ] **Test "Forgot Password"** link

**Expected Results**: ✅ Login system secure and functional

### 1.3 Session Management
- [ ] **Test session persistence**:
  - [ ] Login and navigate pages
  - [ ] Close browser tab, reopen
  - [ ] Verify still logged in
- [ ] **Test logout**:
  - [ ] Click logout button
  - [ ] Verify redirect to public page
  - [ ] Try accessing protected page → Redirect to login
- [ ] **Test session timeout** (wait 1 hour or modify config):
  - [ ] Leave session idle
  - [ ] Try accessing protected page
  - [ ] Verify session expired

**Expected Results**: ✅ Sessions managed securely

### 1.4 Password Security
- [ ] **Test password change**:
  - [ ] Navigate to profile/settings
  - [ ] Change password with valid data
  - [ ] Logout and login with new password
- [ ] **Test password reset**:
  - [ ] Request password reset
  - [ ] Check email for reset link
  - [ ] Follow reset process
  - [ ] Login with new password

**Expected Results**: ✅ Password operations secure

---

## 🔄 **CATEGORY 2: FILE CONVERSION FUNCTIONALITY**

### 2.1 Image Converter Testing

#### Basic Image Conversion:
- [ ] **Navigate to Image Converter** (`/image-converter`)
- [ ] **Test PNG to JPG conversion**:
  - [ ] Upload PNG file (< 100MB)
  - [ ] Select JPG output format
  - [ ] Click Convert
  - [ ] Verify conversion success
  - [ ] Download converted file
  - [ ] Verify file opens correctly
- [ ] **Test JPG to PNG conversion**
- [ ] **Test WEBP conversions**
- [ ] **Test other supported formats**

#### Advanced Image Features:
- [ ] **Test image quality settings**:
  - [ ] Low quality conversion
  - [ ] High quality conversion
  - [ ] Compare file sizes
- [ ] **Test batch conversion** (if available):
  - [ ] Upload multiple files
  - [ ] Convert all at once
  - [ ] Verify all downloads work

**Expected Results**: ✅ All image conversions work correctly

### 2.2 RAW Image Processing
- [ ] **Navigate to RAW Converter** (`/raw-jpg`)
- [ ] **Test RAW to JPG** (if you have RAW files):
  - [ ] Upload CR2, NEF, or DNG file
  - [ ] Select output format
  - [ ] Test conversion
  - [ ] Verify high quality output
- [ ] **Test RAW analysis feature** (if available)
- [ ] **Test RAW preview generation**

**Expected Results**: ✅ RAW processing functional (if files available)

### 2.3 PDF Converter Testing
- [ ] **Navigate to PDF Converter** (`/pdf-converter`)
- [ ] **Test PDF to DOCX**:
  - [ ] Upload PDF with text
  - [ ] Convert to DOCX
  - [ ] Verify document opens in Word
  - [ ] Check text extraction accuracy
- [ ] **Test PDF to CSV**:
  - [ ] Upload PDF with tables
  - [ ] Convert to CSV
  - [ ] Verify data structure

**Expected Results**: ✅ PDF conversions maintain data integrity

### 2.4 Document Converter Testing
- [ ] **Navigate to Document Converter** (`/document-converter`)
- [ ] **Test DOCX to PDF**:
  - [ ] Upload DOCX file
  - [ ] Convert to PDF
  - [ ] Verify formatting preserved
- [ ] **Test DOC to PDF**
- [ ] **Test RTF conversions**

**Expected Results**: ✅ Document formatting preserved

### 2.5 Excel Converter Testing
- [ ] **Navigate to Excel Converter** (`/excel-converter`)
- [ ] **Test XLSX to CSV**:
  - [ ] Upload Excel file with data
  - [ ] Convert to CSV
  - [ ] Verify data accuracy
- [ ] **Test XLSX to JSON**:
  - [ ] Convert Excel to JSON
  - [ ] Verify JSON structure
  - [ ] Check data types maintained

**Expected Results**: ✅ Data conversion accurate

---

## 🛠️ **CATEGORY 3: PDF TOOLS FUNCTIONALITY**

### 3.1 PDF Editor
- [ ] **Navigate to PDF Editor** (`/pdf-editor`)
- [ ] **Test PDF upload and display**:
  - [ ] Upload PDF file
  - [ ] Verify all pages display
  - [ ] Test page navigation
- [ ] **Test annotation features**:
  - [ ] Add text annotations
  - [ ] Draw/highlight
  - [ ] Test different colors
- [ ] **Test save functionality**:
  - [ ] Save edited PDF
  - [ ] Download and verify changes

**Expected Results**: ✅ PDF editing works smoothly

### 3.2 PDF Merge
- [ ] **Navigate to PDF Merge** (`/pdf-merge`)
- [ ] **Test merging multiple PDFs**:
  - [ ] Upload 2-3 PDF files
  - [ ] Arrange in desired order
  - [ ] Merge files
  - [ ] Verify merged PDF contains all pages

**Expected Results**: ✅ PDF merge creates single file

### 3.3 PDF Page Delete
- [ ] **Navigate to PDF Page Delete** (`/pdf-page-delete`)
- [ ] **Test page deletion**:
  - [ ] Upload multi-page PDF
  - [ ] Select pages to delete
  - [ ] Process deletion
  - [ ] Verify correct pages removed

**Expected Results**: ✅ Specific pages removed correctly

### 3.4 Secure PDF
- [ ] **Navigate to Secure PDF** (`/secure-pdf`)
- [ ] **Test password protection**:
  - [ ] Upload PDF
  - [ ] Add password protection
  - [ ] Try opening without password → Denied
  - [ ] Try opening with password → Success
- [ ] **Test password removal**:
  - [ ] Remove password from protected PDF
  - [ ] Verify file opens without password

**Expected Results**: ✅ PDF security features functional

---

## 🗜️ **CATEGORY 4: UTILITY TOOLS**

### 4.1 File Compressor
- [ ] **Navigate to Compressor** (`/compressor`)
- [ ] **Test image compression**:
  - [ ] Upload large image
  - [ ] Select compression level
  - [ ] Compress file
  - [ ] Verify size reduction
  - [ ] Check quality maintained
- [ ] **Test PDF compression**
- [ ] **Test batch compression**

**Expected Results**: ✅ Files compressed without quality loss

### 4.2 Image Cropper
- [ ] **Navigate to Cropper** (`/cropper`)
- [ ] **Test image cropping**:
  - [ ] Upload image
  - [ ] Select crop area
  - [ ] Apply crop
  - [ ] Verify cropped area accurate
- [ ] **Test aspect ratio presets**
- [ ] **Test PDF cropping** (if supported)

**Expected Results**: ✅ Cropping accurate and intuitive

### 4.3 OCR Text Extraction
- [ ] **Navigate to OCR** (`/text-ocr`)
- [ ] **Test text extraction**:
  - [ ] Upload image with text
  - [ ] Extract text
  - [ ] Verify text accuracy
  - [ ] Test different image qualities

**Expected Results**: ✅ Text extraction reasonably accurate

---

## 📊 **CATEGORY 5: USER DASHBOARD & ADMIN**

### 5.1 User Dashboard
- [ ] **Navigate to Dashboard** (`/dashboard`)
- [ ] **Test dashboard display**:
  - [ ] View conversion history
  - [ ] Check usage statistics
  - [ ] Verify file counts
- [ ] **Test profile management**:
  - [ ] Update profile information
  - [ ] Change settings
  - [ ] Verify changes saved

**Expected Results**: ✅ Dashboard shows accurate user data

### 5.2 Admin Panel (if admin user)
- [ ] **Navigate to Admin** (`/admin`)
- [ ] **Test user management**:
  - [ ] View all users
  - [ ] Check user statistics
  - [ ] Test user actions (if safe)
- [ ] **Test system monitoring**:
  - [ ] View conversion logs
  - [ ] Check system health
  - [ ] Review usage analytics

**Expected Results**: ✅ Admin functions work properly

---

## 🌐 **CATEGORY 6: USER INTERFACE & EXPERIENCE**

### 6.1 Navigation Testing
- [ ] **Test main navigation**:
  - [ ] All menu links work
  - [ ] Dropdown menus function
  - [ ] Mobile menu works (resize window)
- [ ] **Test breadcrumbs** (if present)
- [ ] **Test search functionality** (if present)

**Expected Results**: ✅ Navigation intuitive and functional

### 6.2 Responsive Design
- [ ] **Test mobile responsiveness**:
  - [ ] Resize browser to mobile size
  - [ ] Test navigation menu
  - [ ] Test file upload on mobile
  - [ ] Verify buttons accessible
- [ ] **Test tablet view**
- [ ] **Test different screen resolutions**

**Expected Results**: ✅ Site works on all device sizes

### 6.3 User Feedback & Messages
- [ ] **Test success messages**:
  - [ ] Convert file → Success message shown
  - [ ] Login → Welcome message
  - [ ] Form submission → Confirmation
- [ ] **Test error messages**:
  - [ ] Invalid file type → Clear error
  - [ ] Network error → Helpful message
  - [ ] Form errors → Specific guidance
- [ ] **Test loading indicators**:
  - [ ] File upload shows progress
  - [ ] Conversion shows loading
  - [ ] Forms show processing state

**Expected Results**: ✅ User feedback clear and helpful

---

## 🔒 **CATEGORY 7: SECURITY TESTING**

### 7.1 File Upload Security
- [ ] **Test file type restrictions**:
  - [ ] Try uploading .exe file → Rejected
  - [ ] Try uploading .bat file → Rejected
  - [ ] Try uploading .php file → Rejected
  - [ ] Verify only allowed types accepted
- [ ] **Test file size limits**:
  - [ ] Upload very large file → Proper error
  - [ ] Upload normal file → Accepted
- [ ] **Test malicious filenames**:
  - [ ] Files with special characters
  - [ ] Files with very long names

**Expected Results**: ✅ Only safe files accepted

### 7.2 CSRF Protection Testing
- [ ] **Test form submissions**:
  - [ ] Submit forms normally → Works
  - [ ] Try direct POST without CSRF → Blocked
  - [ ] Verify CSRF tokens present in forms
- [ ] **Test login CSRF protection**

**Expected Results**: ✅ CSRF tokens protect forms

### 7.3 Session Security Testing
- [ ] **Test concurrent sessions**:
  - [ ] Login from two browsers
  - [ ] Verify both sessions work
- [ ] **Test session hijacking protection**:
  - [ ] Check secure cookie flags
  - [ ] Verify HttpOnly flags set

**Expected Results**: ✅ Sessions secure

---

## ⚡ **CATEGORY 8: PERFORMANCE TESTING**

### 8.1 Load Time Testing
- [ ] **Test page load speeds**:
  - [ ] Home page loads < 3 seconds
  - [ ] Converter pages load < 3 seconds
  - [ ] Static assets load quickly
- [ ] **Test with slow network**:
  - [ ] Simulate slow connection
  - [ ] Verify graceful degradation

**Expected Results**: ✅ Pages load quickly

### 8.2 Conversion Performance
- [ ] **Test conversion speeds**:
  - [ ] Small files convert quickly
  - [ ] Medium files convert reasonably
  - [ ] Large files show progress
- [ ] **Test concurrent conversions**:
  - [ ] Start multiple conversions
  - [ ] Verify all complete successfully

**Expected Results**: ✅ Conversions complete in reasonable time

---

## 🛠️ **CATEGORY 9: ERROR HANDLING**

### 9.1 Network Error Testing
- [ ] **Simulate network issues**:
  - [ ] Disconnect internet during conversion
  - [ ] Verify graceful error handling
  - [ ] Check user receives helpful message
- [ ] **Test server errors**:
  - [ ] Access invalid URL → 404 page
  - [ ] Force 500 error → Error page shown

**Expected Results**: ✅ Errors handled gracefully

### 9.2 File Processing Errors
- [ ] **Test corrupted files**:
  - [ ] Upload corrupted image
  - [ ] Verify error message clear
  - [ ] System remains stable
- [ ] **Test unsupported files**:
  - [ ] Try converting unsupported format
  - [ ] Verify clear rejection message

**Expected Results**: ✅ Processing errors handled well

---

## 📝 **TEST FILES REQUIRED**

Prepare these test files before starting:

### Images:
- [ ] Small PNG (< 1MB)
- [ ] Large JPG (10-20MB)  
- [ ] WEBP file
- [ ] HEIC file (if available)
- [ ] RAW file: CR2, NEF, or DNG (if available)
- [ ] Corrupted image file

### Documents:
- [ ] Simple PDF with text
- [ ] PDF with tables/data
- [ ] Multi-page PDF (5+ pages)
- [ ] DOCX with formatting
- [ ] Excel file with data (XLSX)
- [ ] PowerPoint presentation

### Special Files:
- [ ] Very large file (> 100MB) for size testing
- [ ] File with special characters in name
- [ ] Empty file
- [ ] Executable file (.exe) for security testing

---

## 📊 **TESTING REPORT TEMPLATE**

### Overall Results:
- **Total Tests Performed**: ___/___
- **Tests Passed**: ___
- **Tests Failed**: ___
- **Critical Issues**: ___
- **Minor Issues**: ___

### Category Results:
- [ ] **Authentication & Security**: ___% Pass
- [ ] **File Conversion**: ___% Pass
- [ ] **PDF Tools**: ___% Pass
- [ ] **Utility Tools**: ___% Pass
- [ ] **User Interface**: ___% Pass
- [ ] **Performance**: ___% Pass
- [ ] **Error Handling**: ___% Pass

### Issues Found:
1. **Issue**: ________________
   **Severity**: Critical/Major/Minor
   **Steps to Reproduce**: ________________
   
2. **Issue**: ________________
   **Severity**: Critical/Major/Minor
   **Steps to Reproduce**: ________________

### Overall Assessment:
- [ ] **Production Ready** (95%+ pass rate)
- [ ] **Needs Minor Fixes** (85-94% pass rate)
- [ ] **Needs Major Fixes** (70-84% pass rate)
- [ ] **Not Ready** (<70% pass rate)

---

## 🚀 **PRODUCTION READINESS CRITERIA**

Your application is **Production Ready** if:
- ✅ **90%+ of tests pass**
- ✅ **No critical security issues**
- ✅ **No data corruption issues**
- ✅ **Error handling works properly**
- ✅ **Performance acceptable**
- ✅ **User experience smooth**

**Recommendation**: Complete this checklist systematically and address any issues found before production deployment.

---

*Manual testing completed by: ________________*  
*Date: ________________*  
*Time spent: ________________*  
*Browser used: ________________*

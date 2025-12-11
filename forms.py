"""
WTForms for Cropio SaaS Platform - Phase 2
Form validation for authentication and user management
"""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, SelectField, DateField, FileField, IntegerField, DecimalField, HiddenField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Optional, Regexp, NumberRange
from wtforms.widgets import TextArea
from flask_wtf.file import FileField, FileAllowed

from models import User

class RegistrationForm(FlaskForm):
    """User registration form"""
    username = StringField('Username', validators=[
        DataRequired(message='Username is required'),
        Length(min=3, max=20, message='Username must be between 3 and 20 characters')
    ])
    
    email = StringField('Email Address', validators=[
        DataRequired(message='Email is required'),
        Email(message='Please enter a valid email address')
    ])
    
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required'),
        Length(min=6, message='Password must be at least 6 characters long')
    ])
    
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(message='Please confirm your password'),
        EqualTo('password', message='Passwords must match')
    ])
    
    terms_accepted = BooleanField('I agree to the Terms of Service and Privacy Policy', validators=[
        DataRequired(message='You must accept the terms to register')
    ])
    
    submit = SubmitField('Register')
    
    def validate_username(self, username):
        """Check if username is already taken"""
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already exists. Please choose a different one.')
    
    def validate_email(self, email):
        """Check if email is already registered"""
        user = User.query.filter_by(email=email.data.lower()).first()
        if user:
            raise ValidationError('Email already registered. Please use a different email or login.')


class LoginForm(FlaskForm):
    """User login form"""
    username_or_email = StringField('Username or Email', validators=[
        DataRequired(message='Please enter your username or email')
    ])
    
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required')
    ])
    
    remember_me = BooleanField('Remember Me')
    
    submit = SubmitField('Login')


class EditProfileForm(FlaskForm):
    """Edit user profile form"""
    username = StringField('Username', validators=[
        DataRequired(message='Username is required'),
        Length(min=3, max=20, message='Username must be between 3 and 20 characters')
    ])
    
    email = StringField('Email Address', validators=[
        DataRequired(message='Email is required'),
        Email(message='Please enter a valid email address')
    ])
    
    current_password = PasswordField('Current Password (required for changes)')
    
    new_password = PasswordField('New Password (leave blank to keep current)', validators=[
        Length(min=6, message='Password must be at least 6 characters long')
    ])
    
    confirm_password = PasswordField('Confirm New Password', validators=[
        EqualTo('new_password', message='Passwords must match')
    ])
    
    submit = SubmitField('Update Profile')
    
    def __init__(self, current_user, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.current_user = current_user
    
    def validate_username(self, username):
        """Check if username is already taken by another user"""
        if username.data != self.current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('Username already exists. Please choose a different one.')
    
    def validate_email(self, email):
        """Check if email is already registered by another user"""
        if email.data.lower() != self.current_user.email:
            user = User.query.filter_by(email=email.data.lower()).first()
            if user:
                raise ValidationError('Email already registered. Please use a different email.')
    
    def validate_current_password(self, current_password):
        """Validate current password if user wants to change password or email"""
        if self.new_password.data or self.email.data.lower() != self.current_user.email:
            if not current_password.data:
                raise ValidationError('Current password is required to make changes.')
            if not self.current_user.check_password(current_password.data):
                raise ValidationError('Current password is incorrect.')


class ChangePasswordForm(FlaskForm):
    """Change password form"""
    current_password = PasswordField('Current Password', validators=[
        DataRequired(message='Current password is required')
    ])
    
    new_password = PasswordField('New Password', validators=[
        DataRequired(message='New password is required'),
        Length(min=6, message='Password must be at least 6 characters long')
    ])
    
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(message='Please confirm your new password'),
        EqualTo('new_password', message='Passwords must match')
    ])
    
    submit = SubmitField('Change Password')


class DeleteAccountForm(FlaskForm):
    """Delete account confirmation form"""
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required to delete your account')
    ])
    
    confirm_delete = BooleanField('I understand this action is permanent and irreversible', validators=[
        DataRequired(message='You must confirm account deletion')
    ])
    
    feedback = TextAreaField('Feedback (Optional)', description='Tell us why you\'re leaving (optional)')
    
    submit = SubmitField('Delete My Account')


class RequestPasswordResetForm(FlaskForm):
    """Password reset request form"""
    email = StringField('Email Address', validators=[
        DataRequired(message='Email is required'),
        Email(message='Please enter a valid email address')
    ])
    
    submit = SubmitField('Send Reset Link')
    
    def validate_email(self, email):
        """Check if email exists in system"""
        user = User.query.filter_by(email=email.data.lower()).first()
        if not user:
            raise ValidationError('No account found with this email address.')


class ResetPasswordForm(FlaskForm):
    """Password reset form"""
    password = PasswordField('New Password', validators=[
        DataRequired(message='Password is required'),
        Length(min=6, message='Password must be at least 6 characters long')
    ])
    
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(message='Please confirm your password'),
        EqualTo('password', message='Passwords must match')
    ])
    
    submit = SubmitField('Reset Password')


class ContactForm(FlaskForm):
    """Contact/Support form"""
    name = StringField('Name', validators=[
        DataRequired(message='Name is required'),
        Length(min=2, max=50, message='Name must be between 2 and 50 characters')
    ])
    
    email = StringField('Email Address', validators=[
        DataRequired(message='Email is required'),
        Email(message='Please enter a valid email address')
    ])
    
    subject = SelectField('Subject', choices=[
        ('', 'Select a topic'),
        ('general', 'General Inquiry'),
        ('technical', 'Technical Support'),
        ('billing', 'Billing Question'),
        ('feature', 'Feature Request'),
        ('bug', 'Bug Report'),
        ('other', 'Other')
    ], validators=[DataRequired(message='Please select a subject')])
    
    message = TextAreaField('Message', validators=[
        DataRequired(message='Message is required'),
        Length(min=10, max=1000, message='Message must be between 10 and 1000 characters')
    ], widget=TextArea())
    
    submit = SubmitField('Send Message')


class CompleteProfileForm(FlaskForm):
    """Complete user profile form with all personal details"""
    # Basic Information
    first_name = StringField('First Name', validators=[
        Optional(),
        Length(max=50, message='First name must not exceed 50 characters')
    ])
    
    last_name = StringField('Last Name', validators=[
        Optional(),
        Length(max=50, message='Last name must not exceed 50 characters')
    ])
    
    display_name = StringField('Display Name', validators=[
        Optional(),
        Length(max=100, message='Display name must not exceed 100 characters')
    ])
    
    phone = StringField('Phone Number', validators=[
        Optional(),
        Length(max=20, message='Phone number must not exceed 20 characters'),
        Regexp(r'^[\+]?[1-9][\d\s\-\(\)]*$', message='Please enter a valid phone number')
    ])
    
    date_of_birth = DateField('Date of Birth', validators=[Optional()])
    
    # Profile Information
    bio = TextAreaField('Bio', validators=[
        Optional(),
        Length(max=500, message='Bio must not exceed 500 characters')
    ])
    
    profile_picture = FileField('Profile Picture', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')
    ])
    
    # Address Information
    address_line1 = StringField('Address Line 1', validators=[
        Optional(),
        Length(max=100, message='Address line 1 must not exceed 100 characters')
    ])
    
    address_line2 = StringField('Address Line 2', validators=[
        Optional(),
        Length(max=100, message='Address line 2 must not exceed 100 characters')
    ])
    
    city = StringField('City', validators=[
        Optional(),
        Length(max=50, message='City must not exceed 50 characters')
    ])
    
    state_province = StringField('State/Province', validators=[
        Optional(),
        Length(max=50, message='State/Province must not exceed 50 characters')
    ])
    
    postal_code = StringField('Postal Code', validators=[
        Optional(),
        Length(max=20, message='Postal code must not exceed 20 characters')
    ])
    
    country = SelectField('Country', choices=[
        ('', 'Select Country'),
        ('US', 'United States'),
        ('CA', 'Canada'),
        ('GB', 'United Kingdom'),
        ('IN', 'India'),
        ('AU', 'Australia'),
        ('DE', 'Germany'),
        ('FR', 'France'),
        ('JP', 'Japan'),
        ('BR', 'Brazil'),
        ('Other', 'Other')
    ], validators=[Optional()])
    
    # Preferences
    timezone = SelectField('Timezone', choices=[
        ('UTC', 'UTC'),
        ('US/Eastern', 'US/Eastern'),
        ('US/Central', 'US/Central'),
        ('US/Mountain', 'US/Mountain'),
        ('US/Pacific', 'US/Pacific'),
        ('Europe/London', 'Europe/London'),
        ('Europe/Paris', 'Europe/Paris'),
        ('Europe/Berlin', 'Europe/Berlin'),
        ('Asia/Kolkata', 'Asia/Kolkata'),
        ('Asia/Tokyo', 'Asia/Tokyo'),
        ('Australia/Sydney', 'Australia/Sydney')
    ], default='UTC', validators=[Optional()])
    
    language = SelectField('Language', choices=[
        ('en', 'English'),
        ('es', 'Spanish'),
        ('fr', 'French'),
        ('de', 'German'),
        ('it', 'Italian'),
        ('pt', 'Portuguese'),
        ('ja', 'Japanese'),
        ('ko', 'Korean'),
        ('zh', 'Chinese'),
        ('hi', 'Hindi')
    ], default='en', validators=[Optional()])
    
    # Notification Preferences
    email_notifications = BooleanField('Email Notifications', default=True)
    marketing_emails = BooleanField('Marketing Emails', default=False)
    sms_notifications = BooleanField('SMS Notifications', default=False)
    
    submit = SubmitField('Update Complete Profile')
    
    def __init__(self, current_user, *args, **kwargs):
        super(CompleteProfileForm, self).__init__(*args, **kwargs)
        self.current_user = current_user


class UserPreferencesForm(FlaskForm):
    """User preferences and settings form"""
    timezone = SelectField('Timezone', choices=[
        ('UTC', 'UTC'),
        ('US/Eastern', 'US/Eastern'),
        ('US/Central', 'US/Central'),
        ('US/Mountain', 'US/Mountain'),
        ('US/Pacific', 'US/Pacific'),
        ('Europe/London', 'Europe/London'),
        ('Europe/Paris', 'Europe/Paris'),
        ('Europe/Berlin', 'Europe/Berlin'),
        ('Asia/Kolkata', 'Asia/Kolkata'),
        ('Asia/Tokyo', 'Asia/Tokyo'),
        ('Australia/Sydney', 'Australia/Sydney')
    ], default='UTC')
    
    language = SelectField('Language', choices=[
        ('en', 'English'),
        ('es', 'Spanish'),
        ('fr', 'French'),
        ('de', 'German'),
        ('it', 'Italian'),
        ('pt', 'Portuguese'),
        ('ja', 'Japanese'),
        ('ko', 'Korean'),
        ('zh', 'Chinese'),
        ('hi', 'Hindi')
    ], default='en')
    
    email_notifications = BooleanField('Email Notifications', default=True)
    marketing_emails = BooleanField('Marketing Emails', default=False)
    sms_notifications = BooleanField('SMS Notifications', default=False)
    
    submit = SubmitField('Save Preferences')


class AdminUserManagementForm(FlaskForm):
    """Admin form for user management"""
    username = StringField('Username', validators=[
        DataRequired(message='Username is required'),
        Length(min=3, max=20, message='Username must be between 3 and 20 characters')
    ])
    
    email = StringField('Email Address', validators=[
        DataRequired(message='Email is required'),
        Email(message='Please enter a valid email address')
    ])
    
    role = SelectField('User Role', choices=[
        ('user', 'Regular User'),
        ('staff', 'Staff Member'),
        ('admin', 'Administrator')
    ], default='user')
    
    subscription_tier = SelectField('Subscription Tier', choices=[
        ('free', 'Free'),
        ('premium', 'Premium')
    ], default='free')
    
    is_active = BooleanField('Account Active', default=True)
    email_verified = BooleanField('Email Verified', default=False)
    account_locked = BooleanField('Account Locked', default=False)
    lock_reason = StringField('Lock Reason (if locked)', validators=[Optional()])
    
    submit = SubmitField('Update User')


# Form validation helpers
def validate_strong_password(form, field):
    """Custom validator for strong password"""
    password = field.data
    if not password:
        return
    
    errors = []
    if len(password) < 8:
        errors.append('Password must be at least 8 characters long')
    if not any(c.isupper() for c in password):
        errors.append('Password must contain at least one uppercase letter')
    if not any(c.islower() for c in password):
        errors.append('Password must contain at least one lowercase letter')
    if not any(c.isdigit() for c in password):
        errors.append('Password must contain at least one number')
    
    if errors:
        raise ValidationError('. '.join(errors))


# Converter Forms for file upload with CSRF protection

class BaseConverterForm(FlaskForm):
    """Base form for all file converters"""
    file = FileField('Select File', validators=[
        DataRequired(message='Please select a file to convert')
    ])
    submit = SubmitField('Convert File')


class ImageConverterForm(BaseConverterForm):
    """Image converter form with format selection"""
    format = SelectField('Convert to:', choices=[
        ('png', 'PNG'),
        ('jpg', 'JPG'),
        ('webp', 'WEBP'),
        ('gif', 'GIF'),
        ('pdf', 'PDF'),
        ('ico', 'ICO'),
        ('bmp', 'BMP'),
        ('tiff', 'TIFF')
    ], default='png')


class PDFConverterForm(BaseConverterForm):
    """PDF converter form with format selection"""
    format = SelectField('Convert to:', choices=[
        ('docx', 'DOCX - Word Document'),
        ('txt', 'TXT - Plain Text'),
        ('csv', 'CSV - Comma Separated Values'),
        ('md', 'MD - Markdown'),
        ('html', 'HTML - Web Page'),
        ('json', 'JSON - JavaScript Object Notation'),
        ('xml', 'XML - Extensible Markup Language'),
        ('excel', 'XLSX - Excel Spreadsheet (Tables)'),
        ('images', 'ZIP - Extract All Images'),
        ('structured_text', 'JSON - Structured Text Analysis')
    ], default='docx')


class DocumentConverterForm(BaseConverterForm):
    """Document converter form with format selection"""
    format = SelectField('Convert to:', choices=[
        ('pdf', 'PDF - Portable Document Format'),
        ('txt', 'TXT - Plain Text'),
        ('csv', 'CSV - Comma Separated Values'),
        ('html', 'HTML - Web Page'),
        ('md', 'MD - Markdown'),
        ('xml', 'XML - Extensible Markup Language'),
        ('yaml', 'YAML - YAML Ain\'t Markup Language'),
        ('json', 'JSON - JavaScript Object Notation'),
        ('excel', 'XLSX - Excel Spreadsheet')
    ], default='pdf')


class ExcelConverterForm(BaseConverterForm):
    """Excel converter form with format selection"""
    format = SelectField('Convert to:', choices=[
        ('pdf', 'PDF - Portable Document Format'),
        ('csv', 'CSV - Comma Separated Values'),
        ('html', 'HTML - Web Page'),
        ('json', 'JSON - JavaScript Object Notation'),
        ('xml', 'XML - Extensible Markup Language'),
        ('txt', 'TXT - Plain Text')
    ], default='pdf')


class NotebookConverterForm(BaseConverterForm):
    """Notebook converter form with format selection"""
    format = SelectField('Convert to:', choices=[
        ('html', 'HTML - Web Page'),
        ('pdf', 'PDF - Portable Document Format'),
        ('md', 'MD - Markdown'),
        ('py', 'PY - Python Script'),
        ('tex', 'TEX - LaTeX Document')
    ], default='html')


class TextOCRForm(BaseConverterForm):
    """Text OCR form with format selection"""
    format = SelectField('Convert to:', choices=[
        ('txt', 'TXT - Plain Text'),
        ('pdf', 'PDF - Document'),
        ('docx', 'DOCX - Word Document'),
        ('json', 'JSON - Structured Data')
    ], default='txt')


class CompressorForm(FlaskForm):
    """File compressor form with compression options"""
    files = FileField('Select Files', validators=[
        DataRequired(message='Please select files to compress')
    ])
    
    compression_mode = SelectField('Compression Mode:', choices=[
        ('quality', 'Quality Based'),
        ('size', 'Target File Size')
    ], default='quality')
    
    # Quality-based compression
    quality_level = SelectField('Quality Level:', choices=[
        ('high', 'High Quality (Less Compression)'),
        ('medium', 'Medium Quality (Balanced)'),
        ('low', 'Low Quality (More Compression)')
    ], default='medium')
    
    # Size-based compression
    target_size = SelectField('Target File Size:', choices=[
        ('5', '5 KB'),
        ('10', '10 KB'),
        ('15', '15 KB'),
        ('20', '20 KB'),
        ('30', '30 KB'),
        ('50', '50 KB'),
        ('75', '75 KB'),
        ('100', '100 KB'),
        ('150', '150 KB'),
        ('200', '200 KB'),
        ('300', '300 KB'),
        ('500', '500 KB'),
        ('750', '750 KB'),
        ('1000', '1 MB')
    ], default='100')
    
    submit = SubmitField('Compress Files')


class CropperForm(FlaskForm):
    """Image cropper form with advanced cropping options"""
    files = FileField('Select Image or PDF', validators=[
        DataRequired(message='Please select an image or PDF file to crop')
    ])
    
    # Crop mode selection
    crop_mode = SelectField('Crop Mode:', choices=[
        ('free', 'Free Crop'),
        ('aspect', 'Fixed Aspect Ratio'),
        ('preset', 'Preset Dimensions')
    ], default='free')
    
    # Aspect ratio options
    aspect_ratio = SelectField('Aspect Ratio:', choices=[
        ('free', 'Free (No Constraint)'),
        ('1:1', 'Square (1:1)'),
        ('4:3', 'Standard (4:3)'),
        ('16:9', 'Widescreen (16:9)'),
        ('3:2', 'Photo (3:2)'),
        ('5:4', 'Large Format (5:4)'),
        ('21:9', 'Ultra Wide (21:9)'),
        ('9:16', 'Portrait (9:16)'),
        ('3:4', 'Portrait Standard (3:4)'),
        ('2:3', 'Portrait Photo (2:3)')
    ], default='free')
    
    # Preset dimensions
    preset_dimensions = SelectField('Preset Size:', choices=[
        ('custom', 'Custom Crop'),
        ('1920x1080', '1920×1080 (Full HD)'),
        ('1280x720', '1280×720 (HD)'),
        ('800x600', '800×600 (SVGA)'),
        ('640x480', '640×480 (VGA)'),
        ('1200x1200', '1200×1200 (Square Large)'),
        ('600x600', '600×600 (Square Medium)'),
        ('300x300', '300×300 (Square Small)'),
        ('1024x768', '1024×768 (XGA)'),
        ('512x512', '512×512 (Profile Picture)'),
        ('256x256', '256×256 (Icon)'),
        ('128x128', '128×128 (Thumbnail)')
    ], default='custom')
    
    # Output format
    output_format = SelectField('Output Format:', choices=[
        ('jpeg', 'JPEG - Best for Photos'),
        ('png', 'PNG - Best for Graphics'),
        ('webp', 'WebP - Modern Format'),
        ('pdf', 'PDF - Document Format'),
        ('bmp', 'BMP - Bitmap'),
        ('tiff', 'TIFF - High Quality')
    ], default='jpeg')
    
    # Quality settings (for lossy formats)
    output_quality = SelectField('Output Quality:', choices=[
        ('95', 'Maximum (95%)'),
        ('85', 'High (85%)'),
        ('75', 'Medium (75%)'),
        ('65', 'Low (65%)'),
        ('50', 'Minimum (50%)')
    ], default='85')
    
    # Batch processing
    batch_processing = BooleanField('Enable Batch Processing', default=False)
    
    # Background removal (advanced feature)
    remove_background = BooleanField('Remove Background (AI)', default=False)
    
    # Enhance image
    auto_enhance = BooleanField('Auto Enhance Colors', default=False)
    
    submit = SubmitField('Crop Image')


class PDFEditorForm(FlaskForm):
    """Form for PDF Editor with advanced features and validation"""
    
    # Basic editing options
    operation = SelectField('Operation', choices=[
        ('annotate', 'Annotate PDF'),
        ('extract_text', 'Extract Text'),
        ('insert_image', 'Insert Image'),
        ('split', 'Split Pages'),
        ('merge', 'Merge PDFs'),
        ('rotate', 'Rotate Pages'),
        ('watermark', 'Add Watermark'),
        ('compress', 'Compress PDF'),
        ('encrypt', 'Password Protect')
    ], default='annotate', validators=[DataRequired()])
    
    # Annotation tools
    annotation_tool = SelectField('Annotation Tool', choices=[
        ('select', 'Select Tool'),
        ('text', 'Text Tool'),
        ('draw', 'Freehand Drawing'),
        ('highlight', 'Highlight Text'),
        ('rectangle', 'Rectangle'),
        ('circle', 'Circle'),
        ('arrow', 'Arrow'),
        ('eraser', 'Eraser')
    ], default='select', validators=[DataRequired()])
    
    # Drawing properties
    stroke_color = StringField('Stroke Color', default='#FF0000', validators=[
        Optional(), Regexp(r'^#[0-9A-Fa-f]{6}$', message="Invalid hex color format")
    ])
    
    fill_color = StringField('Fill Color', default='#0000FF', validators=[
        Optional(), Regexp(r'^#[0-9A-Fa-f]{6}$', message="Invalid hex color format")
    ])
    
    line_width = IntegerField('Line Width', default=2, validators=[
        NumberRange(min=1, max=20, message="Line width must be between 1 and 20")
    ])
    
    font_size = IntegerField('Font Size', default=12, validators=[
        NumberRange(min=8, max=72, message="Font size must be between 8 and 72")
    ])
    
    # Text annotation properties
    text_content = TextAreaField('Text Content', validators=[Optional(), Length(max=1000)])
    font_family = SelectField('Font Family', choices=[
        ('helvetica', 'Helvetica'),
        ('times', 'Times Roman'),
        ('courier', 'Courier'),
        ('arial', 'Arial'),
        ('calibri', 'Calibri')
    ], default='helvetica', validators=[Optional()])
    
    # Page manipulation
    target_pages = StringField('Target Pages', validators=[
        Optional(), Regexp(r'^[0-9,\-\s]+$', message="Use format: 1,3,5-10")
    ])
    
    rotation_angle = SelectField('Rotation Angle', choices=[
        ('0', 'No Rotation'),
        ('90', '90° Clockwise'),
        ('180', '180°'),
        ('270', '270° Clockwise')
    ], default='0', validators=[Optional()])
    
    # Split options
    split_method = SelectField('Split Method', choices=[
        ('pages', 'By Page Numbers'),
        ('ranges', 'By Page Ranges'),
        ('bookmark', 'By Bookmarks'),
        ('size', 'By File Size')
    ], default='pages', validators=[Optional()])
    
    page_ranges = TextAreaField('Page Ranges', validators=[
        Optional(), Length(max=500)
    ])
    
    # Watermark options
    watermark_text = StringField('Watermark Text', validators=[
        Optional(), Length(max=100)
    ])
    
    watermark_opacity = DecimalField('Watermark Opacity', default=0.3, validators=[
        Optional(), NumberRange(min=0.1, max=1.0, message="Opacity must be between 0.1 and 1.0")
    ])
    
    watermark_position = SelectField('Watermark Position', choices=[
        ('center', 'Center'),
        ('top_left', 'Top Left'),
        ('top_right', 'Top Right'),
        ('bottom_left', 'Bottom Left'),
        ('bottom_right', 'Bottom Right'),
        ('diagonal', 'Diagonal')
    ], default='center', validators=[Optional()])
    
    # Image insertion
    image_position_x = IntegerField('Image X Position', validators=[
        Optional(), NumberRange(min=0, max=2000)
    ])
    
    image_position_y = IntegerField('Image Y Position', validators=[
        Optional(), NumberRange(min=0, max=2000)
    ])
    
    image_width = IntegerField('Image Width', validators=[
        Optional(), NumberRange(min=10, max=1000)
    ])
    
    image_height = IntegerField('Image Height', validators=[
        Optional(), NumberRange(min=10, max=1000)
    ])
    
    # Security options
    password = StringField('Password Protection', validators=[
        Optional(), Length(min=4, max=50)
    ])
    
    allow_printing = BooleanField('Allow Printing', default=True)
    allow_copying = BooleanField('Allow Copying', default=True)
    allow_modification = BooleanField('Allow Modification', default=False)
    
    # Output settings
    output_filename = StringField('Output Filename', validators=[
        Optional(), Length(max=100), 
        Regexp(r'^[^<>:"/\\|?*]+$', message="Invalid filename characters")
    ])
    
    compression_level = SelectField('Compression Level', choices=[
        ('none', 'No Compression'),
        ('low', 'Low Compression'),
        ('medium', 'Medium Compression'),
        ('high', 'High Compression'),
        ('maximum', 'Maximum Compression')
    ], default='medium', validators=[Optional()])
    
    preserve_quality = BooleanField('Preserve Image Quality', default=True)
    
    # Advanced features
    enable_ocr = BooleanField('Enable OCR (Text Recognition)', default=False)
    ocr_language = SelectField('OCR Language', choices=[
        ('eng', 'English'),
        ('spa', 'Spanish'),
        ('fra', 'French'),
        ('deu', 'German'),
        ('ita', 'Italian'),
        ('por', 'Portuguese'),
        ('rus', 'Russian'),
        ('chi_sim', 'Chinese Simplified'),
        ('chi_tra', 'Chinese Traditional'),
        ('jpn', 'Japanese'),
        ('kor', 'Korean')
    ], default='eng', validators=[Optional()])
    
    auto_save = BooleanField('Auto Save Changes', default=True)
    backup_original = BooleanField('Backup Original File', default=True)
    
    # Form validation and processing flags
    batch_mode = BooleanField('Batch Processing Mode', default=False)
    processing_priority = SelectField('Processing Priority', choices=[
        ('low', 'Low Priority'),
        ('normal', 'Normal Priority'),
        ('high', 'High Priority')
    ], default='normal', validators=[Optional()])
    
    # Hidden fields for JavaScript data
    annotations_data = HiddenField('Annotations Data')
    page_modifications = HiddenField('Page Modifications')
    editor_state = HiddenField('Editor State')
    
    submit = SubmitField('Process PDF')
    
    def validate_target_pages(self, field):
        """Custom validator for target pages format"""
        if field.data:
            try:
                # Parse page ranges like "1,3,5-10,15"
                parts = field.data.replace(' ', '').split(',')
                for part in parts:
                    if '-' in part:
                        start, end = part.split('-', 1)
                        if not (start.isdigit() and end.isdigit()):
                            raise ValueError("Invalid page range")
                        if int(start) > int(end):
                            raise ValueError("Start page must be less than end page")
                    elif not part.isdigit():
                        raise ValueError("Invalid page number")
            except ValueError as e:
                raise ValidationError(f"Invalid page format: {str(e)}")
    
    def validate_page_ranges(self, field):
        """Custom validator for page ranges in split operation"""
        if field.data and self.split_method.data == 'ranges':
            try:
                # Validate JSON format for page ranges
                import json
                ranges = json.loads(field.data)
                if not isinstance(ranges, list):
                    raise ValueError("Page ranges must be a list")
                for page_range in ranges:
                    if not isinstance(page_range, list) or len(page_range) != 2:
                        raise ValueError("Each range must have start and end page")
                    start, end = page_range
                    if not isinstance(start, int) or not isinstance(end, int):
                        raise ValueError("Page numbers must be integers")
                    if start > end:
                        raise ValueError("Start page must be less than end page")
            except (json.JSONDecodeError, ValueError) as e:
                raise ValidationError(f"Invalid page ranges format: {str(e)}")

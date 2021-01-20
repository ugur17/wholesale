from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField, TextAreaField, IntegerField
from wtforms.validators import DataRequired, Length, Email, EqualTo, email_validator
from wtforms.widgets.html5 import NumberInput

WHOIS_CHOICES = [('1', 'customer'), ('2', 'store')]
MATERIAL_CHOICES = [('1', 'wool'), ('2', 'silk'), ('3', 'cotton'), ('4', 'flax'), ('5', 'nylon'), ('6', 'polyester'), ('7', 'acrylic')]
LEVEL_CHOICES = [('1', 'Low Level Priority'), ('2', 'Medium Level Priority'), ('3', 'High Level Priority')]

class RegistrationForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=20)])
    phone = StringField('Phone', validators=[DataRequired(), Length(10)])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    whois = SelectField('Who are you?', choices = WHOIS_CHOICES)
    submit = SubmitField('Sign Up')

class RegistrationDetailForm(FlaskForm):
    store_name = StringField('Store Name', validators=[DataRequired(), Length(min=2, max=30)])
    store_address = TextAreaField('Address', validators=[DataRequired()])
    submit = SubmitField('Confirm')

class LoginForm(FlaskForm):
    phone = StringField('Phone', validators=[DataRequired(), Length(10)])
    password = PasswordField('Password', validators=[DataRequired()])
    whois = SelectField('Who are you?', choices = WHOIS_CHOICES)
    submit = SubmitField('Sign In')

class UpdateCustomerForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=20)])
    phone = StringField('Phone', validators=[DataRequired(), Length(10)])
    picture = FileField('Update Profile Picture', validators = [FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Update')

class UpdateStoreForm(FlaskForm):
    store_name = StringField('Store Name', validators=[DataRequired(), Length(min=2, max=20)])
    store_address = TextAreaField('Store Address', validators=[DataRequired()])
    owner_name = StringField('Owner Name', validators=[DataRequired(), Length(min=2, max=20)])
    phone = StringField('Owner Phone', validators=[DataRequired(), Length(10)])
    picture = FileField('Update Profile Picture', validators = [FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Update')

class ProductForm(FlaskForm):
    name = StringField('Product Name', validators=[DataRequired()])
    material = SelectField('What is the material of this product?', choices = MATERIAL_CHOICES)
    color = StringField('Product Color', validators=[DataRequired()])
    price = IntegerField('Price',validators=[DataRequired()], widget=NumberInput())
    photo = FileField('Update Product Picture', validators = [FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Add Product')

class CartForm(FlaskForm):
    quantity = IntegerField('Quantity',validators=[DataRequired()], widget=NumberInput())
    submit = SubmitField('Add To Cart!')

class SearchForm(FlaskForm):
    who_search = SelectField('Select', choices = WHOIS_CHOICES)
    search = StringField('Search', [DataRequired()])
    submit = SubmitField('Search',
                       render_kw={'class': 'btn btn-success btn-block'})

class PriorityForm(FlaskForm):
    level = SelectField('Select', choices = LEVEL_CHOICES)
    submit = SubmitField('Take Priority')
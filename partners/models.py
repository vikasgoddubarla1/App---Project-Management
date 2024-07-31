from django.db import models
# from locations.models import Role
class Timezone(models.Model):
    zoneName        = models.CharField(max_length=100)
    gmtOffset       = models.CharField(max_length=100)
    gmtOffsetName   = models.CharField(max_length=100)
    abbreviation    = models.CharField(max_length=100)
    tzName          = models.CharField(max_length=100)
    
    def __str__(self):
        return self.zoneName
    

    
class Countries(models.Model):
    name           = models.CharField(max_length=100)
    iso3           = models.CharField(max_length=100)
    iso2           = models.CharField(max_length=100)
    numeric_code   = models.CharField(max_length=100)
    phone_code     = models.CharField(max_length=100)
    capital        = models.CharField(max_length=100)
    currency       = models.CharField(max_length=100)
    currency_symbol= models.CharField(max_length=100)
    tld            = models.CharField(max_length=100)
    native         = models.CharField(max_length=100, null=True)
    region         = models.CharField(max_length=100)
    sub_region     = models.CharField(max_length=100)
    latitude       = models.DecimalField(max_digits=9, decimal_places=6, null=True)
    longitude      = models.DecimalField(max_digits=9, decimal_places=6, null=True)
    emoji          = models.CharField(max_length=100)
    emojiU         = models.CharField(max_length=100)
    translations   = models.JSONField(default=dict) 
    Timezone       = models.ForeignKey(Timezone, on_delete=models.SET_NULL, null=True )
    
    class Meta:
        verbose_name_plural = "Countries"
    
    def __str__(self):
        return self.name
    


class Partner(models.Model):    
    name           = models.CharField(max_length=255, unique=True)
    email          = models.EmailField(max_length=100, unique=True, null=True)
    phone          = models.CharField(max_length=20, unique=True, null=True)
    partner_logo   = models.ImageField(upload_to='partner_logo', null=True, blank=True)
    support_phone  = models.CharField(max_length=20, null=True, blank=True)
    support_email  = models.EmailField(max_length=100, null=True, blank=True)
    sales_phone    = models.CharField(max_length=20, null=True, blank=True)
    sales_email    = models.EmailField(max_length=100, null=True, blank=True)
    address_line_1 = models.CharField(max_length=100, null=True)
    address_line_2 = models.CharField(max_length=100, null=True, blank=True)
    city           = models.CharField(max_length=100, null=True)
    zip_code       = models.IntegerField(null=True, blank=True)
    country_id     = models.ForeignKey(Countries, on_delete=models.SET_NULL, null=True)
    remarks        = models.TextField(max_length=2000, null=True, blank=True)
    role_id         = models.ManyToManyField('locations.Role', null=True, blank=True)
    website         = models.CharField(max_length=555, null=True, blank=True)
    
    def assign_roles_to_users(self, roles):
        for user in self.user_set.all():
            user.role_id.add(*roles)
    
    def remove_roles_to_users(self, roles):
        for user in self.user_set.all():
            user.role_id.remove(*roles)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.role_id.exists():
            self.assign_roles_to_users(self.role_id.all())
    
    
    def __str__(self):
        return self.name
    

class Type(models.Model):
    name = models.CharField(max_length=255, unique=True)
    role_id = models.ForeignKey('locations.Role', on_delete = models.SET_NULL, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    is_fixed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    def __str__(self):
        return self.name

class PartnerType(models.Model):
    partner_id = models.ForeignKey(Partner, on_delete=models.CASCADE)
    type_id    = models.ForeignKey(Type, on_delete = models.CASCADE)
    
    def __str__(self):
        return self.partner_id.name
    
class PartnerTypesRole(models.Model):
    partner_id = models.ForeignKey(Partner, on_delete= models.CASCADE)
    type_id     = models.ForeignKey(Type, on_delete=models.CASCADE)
    role_id     = models.ForeignKey('locations.Role', on_delete = models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return self.partner_id.name
    
class PartnerTypeRolesUser(models.Model):
    partner_types_role_id = models.ForeignKey(PartnerTypesRole, on_delete = models.CASCADE)
    user_id               = models.ForeignKey('usermanagement.User', on_delete=models.CASCADE)
    is_admin              = models.BooleanField(default=False)
    
    def __str__(self):
        return self.partner_types_role_id.partner_id.name
from django.db import models
from usermanagement.models import User
from partners.models import *
from contracts.models import Contract
from django.core.exceptions import ValidationError


from django.core.validators import FileExtensionValidator

class Status(models.Model):
    name = models.CharField(max_length=100, blank=True)
    
    class Meta:
        verbose_name_plural = "Status"
    def __str__(self):
        return self.name


class LocationStatusEVPV(models.Model):
    name = models.CharField(max_length=160, null=True, blank=True)
    
    def __str__(self):
        return self.name
    


def validate_file_size(value):
    max_size = 10 * 1024 * 1024  # 5 MB
    if value.size > max_size:
        raise ValidationError(("location image must be less than 10MB"))
    
def location_image(instance, filename):
    filename = f"location_image_{instance.id}{filename[-4:]}"
    return f"location_images/{filename}"
class Location(models.Model):
  
    status_id       = models.ForeignKey(Status, on_delete=models.SET_NULL, null=True, blank= True)
    name            = models.CharField(max_length=100)#
    description     = models.TextField(null=True)
    micro_page_image = models.FileField(upload_to='magic_page_image', blank=True, null=True, validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png']), 
            validate_file_size,
        ],
    )
    address_line_1  = models.CharField(max_length=160, null=True, blank=True)#
    address_line_2  = models.CharField(max_length=160, null=True, blank=True)
    zipcode         = models.CharField(max_length=10, null=True, blank=True)#
    city            = models.CharField(max_length=50, null=True, blank=True)#
    state           = models.CharField(max_length=50, null=True, blank=True)
    country_id      = models.ForeignKey(Countries, on_delete=models.SET_NULL, null=True, blank=True)
    sales_email     = models.EmailField(null=True, blank=True)
    sales_phone     = models.CharField(max_length=20, null=True, blank=True)
    support_email   = models.EmailField(null=True, blank=True)
    support_phone   = models.CharField(max_length=20, null=True, blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)
    operating_date = models.DateField(null=True, blank=True)
    land_owner_id   = models.ForeignKey(Partner, on_delete=models.SET_NULL, null=True, blank=True, related_name='owned_location')
    land_owner_asset_id = models.CharField(max_length=100, null=True, blank=True)#asset_id
    property_manager_id = models.ForeignKey(Partner, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_location')#slate_pm
    tenant_id       = models.ForeignKey(Partner, on_delete=models.SET_NULL, null=True, blank=True, related_name='leased_location')#anchor_tenant
    tenant_type     = models.CharField(max_length=55, null=True, blank=True) # tenant_structure
    location_code            = models.CharField(max_length=155, null=True, blank=True)
    location_micropage = models.CharField(max_length=155, null=True, blank=True, unique=True)
    location_state           = models.CharField(max_length=100, null=True, blank=True, choices=[
        ('renovation', 'RENOVATION'),
        ('sale', 'SALE'),
    ])
    snowweight_load_factor     = models.CharField(max_length=100, null=True, blank=True, choices=[
        ('I', 'I'), 
        ('II', 'II'),
        ('III', 'III')
    ])
    current_phase_id = models.ForeignKey('projectmanagement.ProjectPhase', on_delete=models.SET_NULL, null=True, blank=True,)
    estimated_completion_date = models.DateField(null=True, blank=True,)
    estimated_current_phase_end_date = models.DateField(null=True, blank=True,)
    location_image = models.FileField(upload_to='location_image', blank=True, null=True, validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png']), 
            validate_file_size,
        ],
    )
    location_device_image = models.FileField(upload_to='location_device_image', blank=True, null=True, validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png']),  
            validate_file_size,
        ],
    )
    channel_background_color = models.CharField(max_length=255, null=True, blank=True)
    channel_text_color = models.CharField(max_length=255, blank=True, null=True)
    current_phase       = models.CharField(max_length=100, null=True, blank=True)
    current_phase_status = models.CharField(max_length=100, null=True, blank=True)
    location_status = models.CharField(max_length=100, default='pipeline', choices=[
        ('pipeline', 'PIPELINE'), 
        ('projectmanagement', 'PROJECTMANAGEMENT'),
        ('operating', 'OPERATING')
    ])
    location_latitude = models.CharField(max_length=100, null=True, blank=True)
    location_longitude = models.CharField(max_length=100, null=True, blank=True)
    prioritisation        = models.BooleanField(default='False')
    prioritisation_comments  = models.TextField(null=True, blank=True)
    state_start_date      = models.DateField(null=True, blank=True)
    state_end_date        = models.DateField(null=True, blank=True)
    state_comments         = models.TextField(null=True, blank=True)
    expected_kWp           = models.CharField(max_length=160, null=True, blank=True)
    estimated_pv_costs    = models.CharField(max_length=160, null=True, blank=True)
    LIS                    = models.JSONField(null=True, blank=True) #(AC, DC, BATTERY)
    #Newly added fields
    project_number          = models.CharField(max_length=100, null=True, blank=True)
    status_ev_id               = models.ForeignKey(LocationStatusEVPV, on_delete=models.SET_NULL,  null=True, blank=True, related_name = 'status_ev')
    approval_ev             = models.CharField(max_length=100, null=True, blank=True)
    milestone_date          = models.DateField(null=True, blank=True)
    disc_reason_ev          = models.CharField(max_length=100, null=True, blank=True)
    planned_ac              = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)##
    ac_speed                = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)###models.CharField(max_length=100, null=True)
    ac_tech_setup           = models.CharField(max_length=100, null=True, blank=True)
    planned_dc              = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)##
    dc_speed                = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)##
    dc_tech_setup           = models.CharField(max_length=100, null=True, blank=True)
    planned_battery         = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)##
    battery_speed           = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)##
    battery_tech_setup      = models.CharField(max_length=100, null=True, blank=True)
    construction_year       = models.IntegerField(null=True, blank=True)##
    construction_quarter    = models.CharField(max_length=100, null=True, blank=True)
    exp_installation_date   = models.DateField(max_length=100, null=True, blank=True)
    planned_installation_date = models.DateField(null=True, blank=True)
    exp_operation_date          = models.DateField( null=True, blank=True)
    capex_spent_to_date         = models.DateField(null=True, blank=True)
    capex_total_expected        = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    subsidy                     = models.CharField(max_length=100, null=True, blank=True)
    asset_management_comments   = models.TextField(null=True, blank=True)
    approval_cs                 = models.CharField(max_length=100, null=True, blank=True)
    pitch_ev                    = models.CharField(max_length=100, null=True, blank=True)
    negotiations_ev             = models.CharField(max_length=100, null=True, blank=True)
    LOI                         = models.CharField(max_length=100, null=True, blank=True)
    setup_ev                    = models.CharField(max_length=100, null=True, blank=True)
    parking_spots               = models.IntegerField(null=True, blank=True)
    construction_ev             = models.CharField(max_length=100, null=True, blank=True)
    installed_ev                = models.CharField(max_length=100, null=True, blank=True)
    operating_ev                = models.CharField(max_length=100, null=True, blank=True)
    invoice_number_ev           = models.CharField(max_length=100, null=True, blank=True)
    project_cluster_pv          = models.CharField(max_length=100, null=True, blank=True)
    status_pv_id                   = models.ForeignKey(LocationStatusEVPV, on_delete=models.SET_NULL,  null=True, blank=True, related_name = 'status_pv')
    asset_management_comments_pv = models.TextField(null=True, blank=True)
    pitch_pv                    = models.CharField(max_length=100, null=True, blank=True)
    negotiations_pv             = models.CharField(max_length=100, null=True, blank=True)
    LOI_pv                         = models.CharField(max_length=100, null=True, blank=True)
    setup_pv                    = models.CharField(max_length=100, null=True, blank=True)
    construction_pv             = models.CharField(max_length=100, null=True, blank=True)
    installed_pv               = models.CharField(max_length=100, null=True, blank=True)
    operating_pv                = models.CharField(max_length=100, null=True, blank=True)
    invoice_number_pv          = models.CharField(max_length=100, null=True, blank=True)
    project_cluster_ev          = models.CharField(max_length=100, null=True, blank=True)
    lead_company                = models.ForeignKey(Partner, on_delete=models.SET_NULL, null=True, related_name='lead_company')
    lead_manager_ev             = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="EV_user")
    #new fields
    approval_pv                 = models.CharField(max_length=100, null=True, blank=True)
    milestone_date_pv           = models.DateField(null=True, blank=True)
    disc_reason_pv              = models.CharField(max_length=100, null=True, blank=True)
    lease_partner_pv            = models.CharField(max_length=100, null=True, blank=True)
    lease_partner_ev            = models.CharField(max_length=100, null=True, blank=True)
    expected_kWp_pv           = models.CharField(max_length=160, null=True, blank=True)
    expected_spec_yield_pv    = models.CharField(max_length=160, null=True, blank=True)
    construction_year_pv      = models.IntegerField(null=True, blank=True)
    construction_quarter_pv    = models.CharField(max_length=100, null=True, blank=True)
    exp_installation_date_pv   = models.DateField(max_length=100, null=True, blank=True)
    planned_installation_date_pv = models.DateField(null=True, blank=True)
    exp_operation_date_pv          = models.DateField( null=True, blank=True)
    capex_spent_to_date_pv         = models.DateField(null=True, blank=True)
    capex_total_expected_pv        = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    offtakers_pv                    = models.CharField(max_length=100, null=True, blank=True)
    lead_manager_pv                 = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="PV_user")
    preffered_charge_client_ev      = models.CharField(max_length=100, null=True, blank=True)
    geap_ev                         = models.CharField(max_length=100, null=True, blank=True) #green electricity advance payment EV (before tax)
    gep_ev                          = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True) #green electricity price EV (before tax)
    cos_pv                          = models.CharField(max_length=100, null=True, blank=True, choices=[('applied', 'APPLIED'), ('approved', 'APPROVED')]) #commercial office status PV (COS PV)
    

    def __str__(self):
        return self.name
    
    
class PVFile(models.Model):
    location_id = models.ForeignKey(Location, on_delete=models.CASCADE, null=True, blank=True)
    pv_file_url = models.FileField(upload_to='files/pvfiles/', null=True)

class LocationSubTenant(models.Model):
    location_id = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True)
    subtenant_id = models.ForeignKey(Partner, on_delete=models.SET_NULL, null=True)
    display_order = models.IntegerField(null=True, blank=True)
    
    
#----------------------------------------------- Modules Models --------------------------------------------------------------------

class Module(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length= 50)
    
    def __str__(self):
        return self.name


class ModulePanel(models.Model):
    name        = models.CharField(max_length=100)
    slug        = models.SlugField(max_length= 150)
    module_id   = models.ForeignKey(Module, on_delete=models.SET_NULL, null=True)
        
    
    def __str__(self):
        return self.name
    

class Permission(models.Model):
    name = models.CharField(max_length=100, unique = True)
    
    def __str__(self):
        return self.name
    
class Role(models.Model):
    name = models.CharField(max_length=100, unique = True)
    description = models.TextField(null=True, blank=True)
    is_fixed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    
    def __str__(self):
        return self.name

class RolesPermissions(models.Model):
    modules_id          = models.ManyToManyField(Module)
    modules_panels_id   = models.ManyToManyField(ModulePanel)
    permissions_id      = models.ManyToManyField(Permission)
    roles_id            = models.ForeignKey(Role, on_delete=models.CASCADE)
    
    class Meta:
        verbose_name_plural = "Roles Permissions"
        

class LocationRole(models.Model):
    locations_id = models.ManyToManyField(Location)
    partners_id = models.ManyToManyField(Partner)
    roles_id    = models.ManyToManyField(Role)
    
    
#------------------------------------------------ Location Contracts ---------------------------------------------------------------

class LocationContract(models.Model):
    location_id = models.ForeignKey(Location, on_delete=models.CASCADE)
    contract_id = models.ManyToManyField(Contract)
    
    
#--------------------------------------------------- Location Device Slots -----------------------------------------------------------

class LocationDeviceSlot(models.Model):
    location_id         = models.ForeignKey(Location, on_delete=models.CASCADE)
    location_device_id  = models.CharField(max_length=100, null=True, blank=True)
    device_channel_id   = models.CharField(max_length=100, null=True, blank=True)
    x_point             = models.CharField(max_length=100, null=True, blank=True)
    y_point             = models.CharField(max_length=100, null=True, blank=True)
    formula             = models.CharField(max_length=255, null=True, blank=True)
    formula_condition   = models.CharField(max_length=255, null=True, blank=True)
    formula_condition_value = models.CharField(max_length=255, null=True, blank=True)
    

    
class LocationMeasureSettings(models.Model):
    location_id     = models.ForeignKey(Location, on_delete=models.CASCADE)
    grid_op         = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    capex           = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    insurance       = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    billing         = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    energy_meter    = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    direct_marketing= models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    roof_rent       = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    class Meta:
        verbose_name_plural = "Locationmeasuresettings"
    
    def __str__(self):
        return str(self.location_id)
    

class LocationMeasures(models.Model):
    location_id            = models.ForeignKey(Location, on_delete=models.CASCADE)
    device_channel_id      = models.CharField(max_length=100, null=True, blank=True)
    month_year             = models.DateField(null=True, blank=True)
    advance_payment        = models.CharField(max_length=100, null=True, blank=True)
    generated_energy       = models.CharField(max_length=100, null=True, blank=True)
    delivered_energy       = models.CharField(max_length=100, null=True, blank=True)
    created_at             = models.DateTimeField(auto_now_add=True)
    updated_at             = models.DateTimeField(auto_now=True)
    
    
    class Meta:
        verbose_name_plural = "Locationmeasures"
    
    def __str__(self):
        return str(self.location_id)
    
    
class LocationMalos(models.Model):
    location_id = models.ForeignKey(Location, on_delete=models.CASCADE)
    malo_number = models.CharField(max_length=155, null=True, blank=True)
    is_external = models.BooleanField(default=False)
    energy_type = models.CharField(max_length=100, null=True, blank=True, choices=[
        ('infeed', 'INFEED'), 
        ('consumption', 'CONSUMPTION')
    ])
    date_column = models.CharField(max_length=155, null=True, blank=True)
    time_column  = models.CharField(max_length=155, null=True, blank=True)
    value_column = models.CharField(max_length=155, null=True, blank=True)
    values_from  = models.CharField(max_length=155, null=True, blank=True)
    values_to = models.CharField(max_length=155, null=True, blank=True)
    notation  = models.CharField(max_length=155, null=True, blank=True)
    values_unit = models.CharField(max_length=155, null=True, blank=True)
    values_unit_changed = models.CharField(max_length=155, null=True, blank=True)
    date_representation = models.CharField(max_length=155, null=True, blank=True)
    date_format = models.CharField(max_length=155, null=True, blank=True)
        
    
    
    class Meta:
        verbose_name_plural = 'Locationmalos'
    
    def __str__(self):
        return self.malo_number
    
class LocationMaloValues(models.Model):
    location_malo_id = models.ForeignKey(LocationMalos, on_delete=models.CASCADE)
    value            = models.CharField(max_length=55, null=True, blank=True)
    date             = models.DateField(null=True, blank=True)
    time             = models.TimeField(null=True, blank=True)
    
    class Meta:
        verbose_name_plural = 'Locationmolovalues'
class LocationDeviceMalos(models.Model):
    location_malos_id = models.ForeignKey(LocationMalos, on_delete=models.CASCADE)
    malo_calculation_device_channel_id = models.CharField(max_length=100, null=True, blank=True)
    malo_kpi_device_channel_id = models.CharField(max_length=100, null=True, blank=True)
    
    
    
class LocationPartnerType(models.Model):
    location_id = models.ForeignKey(Location, on_delete = models.CASCADE)
    partner_id = models.ForeignKey(Partner, on_delete = models.CASCADE)
    type_id     = models.ForeignKey(Type, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.location_id.name
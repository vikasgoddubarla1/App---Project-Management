from locations.models import *


def check_permission_user(self, request, obj):
    # partner_user = PartnerTypeRolesUser.objects.filter(user_id = request.user)
    # partner_id = partner_user.values_list('partner_types_role_id__partner_id', 'partner_types_role_id__type_id', 'partner_types_role_id__role_id')
    # print(partner_id.values_list('partner_types_role_id__role_id')[0])
    roles_id = request.user.active_role
    modules = Module.objects.filter(slug=obj[1]).values('id')
    module_id = modules[0]['id']
    modules_panels = ModulePanel.objects.filter(slug=obj[2]).values('id')
    modules_panels_id = modules_panels[0]['id']
    
    role_permission = RolesPermissions.objects.filter(roles_id=roles_id, modules_id=module_id, modules_panels_id=modules_panels_id).values('permissions_id')

    return any(permission['permissions_id'] == obj[3] for permission in role_permission)



# def check_permission_user(self, request, obj):
    
#     partner_id = request.user.partner_id.id
#     roles = LocationRole.objects.filter(locations_id=obj[0], partners_id=partner_id).values('roles_id')
#     roles_id = roles[0]['roles_id']
#     modules = Module.objects.filter(slug=obj[1]).values('id')
#     module_id = modules[0]['id']
#     modules_panels = ModulePanel.objects.filter(slug=obj[2]).values('id')
#     modules_panels_id = modules_panels[0]['id']
#     role_permission = RolesPermissions.objects.filter(roles_id=roles_id, modules_id=module_id, modules_panels_id=modules_panels_id).values('permissions_id')

#     counter = 0
#     for permission in role_permission:
#         if permission['permissions_id'] == obj[3]:
#             counter = 1
    
#     if counter == 1:
#         return True
#     else:    
#         return False






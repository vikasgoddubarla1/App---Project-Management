from django.urls import path
from .views import *
# from rest_framework_simplejwt.views import TokenObtainPairView
# from django.urls import path, include
# import oauth2_provider.views as oauth2_views
# from django.conf import settings
# from .views import ApiEndpoint

urlpatterns = [    
    #--------------------------------------- USER URLS --------------------------------------
    path('v1/user', UserList.as_view(), name = 'user_list'),
    path('v1/user/<int:pk>', UserDetail.as_view(), name = 'user_detail'),
    path('v1/user/register', CreateUser.as_view(), name = 'Createuser'),
    
    #U------------------------ USER LOGIN,LOGOUT, ACCESS AND REFRESH TOKEN URLS -------------
    
    path('v1/login', UserLogin.as_view(), name= 'user_login'),
    path('v1/controllerUser/login', ControllerUserLogin.as_view(), name= 'controller_user_login'),
    # path('v1/token', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('v1/client/refresh', ClientRefreshToken.as_view(), name='token_refresh'),
    path('v1/client/token', TokenViewClient.as_view(), name="token_view" ),
    path('v1/logout', Logout.as_view(), name="logout" ),
    
    #------------------------------- EMAIL AND PASSWORD CHANGE URLS -------------------------
    path('v1/user/changeEmail/<int:pk>', ChangeEmail.as_view(), name = 'change_email'),
    path('v1/user/changePassword/<int:pk>', ChangePassword.as_view(), name = 'change_password'),
    
    #--------------------------------------CUSTOMER URLS-------------------------------------
    path('v1/customer', CustomerList.as_view(), name='Customer List'),
    path('v1/customer/<int:pk>', CustomerDetail.as_view(), name="Customer Details"),
    path('v1/customer/register', CreateCustomer.as_view(), name="Customer Registration" ),
    
    #2FA
    path('v1/verifyTwoFactor/<int:id>', Verify2FA.as_view(), name="Verify-2FA" ),
    path('v1/enableTwoFactor', Enable2FA.as_view(), name="Enable-2FA" ),
    path('v1/loginAfterVerify', LoginAfterVerify.as_view(), name='login-after-verify'),
    path('v1/disable2FA', Disable2FA.as_view(), name='Disable-2FA'), #/<int:id>
    path('v1/generatecode/<int:id>', GenerateRecoveryCodes.as_view(), name='Generate-Recovery-code'),
    path('v1/customer/admin/passwordChange/<int:pk>', AdminPasswordChange.as_view(), name = 'Admin-password-change-customer'),
    
    
    #----------------------------------------- Forgot Password Links -----------------------------------------
    path('v1/user/forgotPassword/emailConfirmation', ForgotPasswordEmailConfirmationAPIView.as_view(), name='forgot-password-email-confirmation'),
    path('v1/user/forgotPassword/codeConfirmation', CodeConfirmationAPIView.as_view(), name='password-code-confirmation'),
    path('v1/user/forgotPassword/changePassword', ChangePasswordAPIView.as_view(), name='change-password-after-confirmation'),
    
    #------------------------------------------ User login logs ---------------------------------------------------------------
    path('v1/user/userLoginLogs/<int:user_id>', UserLoginLogsbyUserId.as_view(), name='User-login-logs'),
    path('v1/user/title', UserTitlesGetList.as_view(), name='user-titles'),
    
    path('v1/user/activeRole/update/<int:pk>', UpdateActiveRoleUser.as_view(), name='active-role-update'),
    path('v1/customer/field/register', CreateCustomerByField.as_view(), name = 'Create-customer-by-field'),
    path('v1/customer/field/<int:partner_id>', CustomerListByPartnerID.as_view(), name = 'list-customer-by-field'),
    
    
]

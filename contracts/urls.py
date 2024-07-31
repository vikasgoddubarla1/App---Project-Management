from django.urls import path
from .views import *



urlpatterns = [
    path('v1/contract/create', CreateContract.as_view(), name='create-contract'),
    path('v1/contract', ContractList.as_view(), name='list-contract'),
    path('v1/contract/general/<int:pk>', ContractGeneralUpdate.as_view(), name='contract-general-update'),
    path('v1/contract/general/delete/<int:pk>', ContractPermanentDelete.as_view(), name='contract-general-delete'),
    path('v1/contract/duration/<int:pk>', ContractDurationUpdateView.as_view(), name='contract-duration-update'),
    path('v1/contract/<int:pk>', ContractDetail.as_view(), name='contract-termination-update'),
    # path('v1/contract/partner/<int:contract_id>', ContractPartnerUpdateView.as_view(), name='contract-termination-update'),
    path('v1/contract/contractGroups/<int:contract_id>', ContractFrameworkCreateView.as_view(), name='contract-framework-update'),
    
    path('v1/files/contractfiles/<int:contract_id>', ContractFileCreate.as_view(), name='contract-file-create'),
    path('v1/files/contractfiles/delete/<int:id>/<int:contract_id>', ContractFileDelete.as_view(), name='contract-file-create'),
    path('v1/contract/category/list', ContractCategoryList.as_view(), name='contract-category-list'),
    path('v1/contract/approvalstatus/<int:pk>', ContractApprovalStatusUpdate.as_view(), name='contract-approval-status'),
    path('v1/contract/location/<int:location_id>', ContractListByLocation.as_view(), name='contract by location'),
    path('v1/contract/logs/<int:contract_id>', ContractLogListByContractID.as_view(), name='contract-logs-by-contractid'),
    
    #------------------------------------------------- CONTRACT APPROVALS -----------------------------------------------------------
    path('v1/contract/approvals/create', ContractApprovalCreate.as_view(), name='contract-approval-create'),
    path('v1/contract/approval/update/<int:pk>', ContractApprovalsIsApprovedUpdate.as_view(), name='contract-isapproved-update'),
    path('v1/contract/approvals/list/<int:contract_id>', ContractApprovalsList.as_view(), name='contract-approvals-by-contractid'),
    path('v1/contract/approvals/delete/<int:pk>', ContractApprovalDelete.as_view(), name='contract-approvals-delete'),
    
    #------------------------------------------------- CONTRACT TRASH AND ACTIVE STATUS --------------------------------------------
    path('v1/contract/trash/<int:pk>', ContractTrashDelete.as_view(), name='contract-trash-delete'),
    path('v1/contract/restore/<int:pk>', ContractRestoreUpdate.as_view(), name='contract-restore'),
]
from django.urls import path
from .views import *



urlpatterns = [
    path('v1/checkList/create', CreateCheckList.as_view(), name='create-check-list'),
    path('v1/checkList', GetCheckList.as_view(), name='get-check-list'),
    path('v1/checkList/update/<int:pk>', CheckListUpdate.as_view(), name='update-check-list'),
    path('v1/checkList/detail/<int:pk>', CheckListDetail.as_view(), name='retrieve-check-list'),
    path('v1/checkList/delete/<int:pk>', CheckListDelete.as_view(), name='delete-check-list'),
    path('v1/checkList/sort', CheckListSorting.as_view(), name='sort-check-list'),
    
    #--------------------------------------- CHECKLIST ITEMS APIS --------------------------------------------------------------------------
    path('v1/checkListItems/create', CreateCheckListItems.as_view(), name='create-check-list-items'),
    path('v1/checkListItems/update/<int:pk>', CheckListItemUpdate.as_view(), name='update-check-list-items'),
    path('v1/checkListItems/delete/<int:pk>', CheckListItemDelete.as_view(), name='update-check-list-items'),
    
    #--------------------------------------- TASK CHECK LIST ------------------------------------------------------------------------------------
    path('v1/taskCheckList/create', CreateTaskCheckList.as_view(), name='create-task-check-list'),
    path('v1/taskCheckList/detail/<int:pk>', TaskCheckListDetail.as_view(), name='detail-task-check-list'),
    path('v1/taskCheckList/taskDetail/<int:task_id>', TaskCheckListDetailByTaskId.as_view(), name='detail-task-check-list-id'),
    path('v1/taskCheckList/list', GetTaskCheckList.as_view(), name='get-task-check-list'),
    path('v1/taskCheckList/delete/<int:pk>', TaskCheckListDelete.as_view(), name='delete-task-check-list'),
    path('v1/taskCheckList/update/<int:pk>', UpdateTaskCheckList.as_view(), name='update-task-check-list'),
    # path('v1/taskCheckList/delete/<int:pk>', CreateTaskCheckList.as_view(), name='create-task-check-list'),
    #-------------------------------------- TASK CHECK LIST ITEMS -----------------------------------------------------------------------------
    
    path('v1/taskCheckListItems/create', CreateTaskCheckListItems.as_view(), name='create-task-check-list-items'),
    path('v1/taskCheckListItems/update/<int:pk>', UpdateTaskCheckListItems.as_view(), name='update-task-check-list-items'),
    path('v1/taskCheckListItems/delete/<int:pk>', DeleteTaskCheckListItems.as_view(), name='delete-task-check-list-items'),
    path('v1/taskCheckListItems/list', GetTaskCheckListItems.as_view(), name='update-task-check-list'),
    path('v1/taskCheckListItems/task/<int:task_id>', GetTaskCheckListItemByTaskID.as_view(), name='update-task-check-list-items-by-task'),
    
    #--------------------------------------- TASK TEMPLATE CHECK LIST ------------------------------------------------------------------------------------
    path('v1/template/taskCheckList/create', CreateTaskTemplateCheckList.as_view(), name='create-task-template-check-list'),
    path('v1/template/taskCheckList/detail/<int:pk>', TaskTemplateCheckListDetail.as_view(), name='detail-task-check-list'),
    path('v1/template/taskCheckList/taskDetail/<int:task_id>', TaskTemplateCheckListDetailByTaskId.as_view(), name='detail-task-template-check-list-id'),
    path('v1/template/taskCheckList/list', GetTaskTemplateCheckList.as_view(), name='get-task-template-check-list'),
    path('v1/template/taskCheckList/delete/<int:pk>', TaskTemplateCheckListDelete.as_view(), name='delete-task-template-check-list'),
    path('v1/template/taskCheckList/update/<int:pk>', UpdateTaskTemplateCheckList.as_view(), name='update-task-template-check-list'),

    #-------------------------------------- TASK TEMPLATE CHECK LIST ITEMS -----------------------------------------------------------------------------
    
    path('v1/template/taskCheckListItems/create', CreateTaskTemplateCheckListItems.as_view(), name='create-task-template-check-list-items'),
    path('v1/template/taskCheckListItems/update/<int:pk>', UpdateTaskTemplateCheckListItems.as_view(), name='update-task-template-check-list-items'),
    path('v1/template/taskCheckListItems/delete/<int:pk>', DeleteTaskTemplateCheckListItems.as_view(), name='delete-task-template-check-list-items'),
    path('v1/template/taskCheckListItems/list', GetTaskTemplateCheckListItems.as_view(), name='update-task-template-check-list'),
    path('v1/template/taskCheckListItems/task/<int:task_id>', GetTaskTemplateCheckListItemByTaskID.as_view(), name='update-task-template-check-list-items-by-task'),
    
    #----------------------------------------------------- TAB ---------------------------------------------------------------------------
    path('v1/tab/create', CreateTab.as_view(), name='create-tab'),
    path('v1/tab/update/<int:pk>', UpdateTab.as_view(), name='update-tab'),
    path('v1/tab/retrieve/<int:pk>', RetrieveTab.as_view(), name='retrieve-tab'),
    path('v1/tab/list', ListTab.as_view(), name='list-tab'),
    path('v1/tab/delete/<int:pk>', DeleteTab.as_view(), name='delete-tab'),
    
    #----------------------------------------------------- FIELDS ---------------------------------------------------------------------------
    path('v1/field/create', CreateField.as_view(), name='create-field'),
    path('v1/field/csv/create', FieldCreateWithCSV.as_view(), name='create-field-csv'),
    path('v1/field/file/create', CreateFieldFromCSV.as_view(), name='create-field-csv'),
    path('v1/field/update/<int:pk>', UpdateField.as_view(), name='update-field'),
    path('v1/field/list', ListField.as_view(), name='list-field'),
    path('v1/field/delete/<int:pk>', DeleteField.as_view(), name='delete-field'),
    path('v1/Field/sort', FieldListSorting.as_view(), name='sort-field'),

    
     #----------------------------------------------------- TAB FIELDS ---------------------------------------------------------------------------
    path('v1/tabFields/create', CreateTabFields.as_view(), name='create-tab-field'),
    path('v1/tabFields/update/<int:pk>', UpdateTabFields.as_view(), name='update-tab-field'),
    path('v1/tabFields/list', ListTabFields.as_view(), name='list-tab-field'),
    path('v1/tabFields/delete/<int:pk>', DeleteTabFields.as_view(), name='delete-tab-field'),
    
    #---------------------------------------------------- LOCATION TAB FIELDS ----------------------------------------------------------------
    path('v1/locationFields/create', CreateLocationFields.as_view(), name='create-location-fields'),
    path('v1/locationFields/update/<int:pk>', UpdateLocationFields.as_view(), name='update-location-fields'),
    path('v1/locationFields/list/<int:location_id>', LocationFieldsListbyLocationID.as_view(), name='list-location-fields-location_id'),
    path('v1/locationFields/list', ListLocationFields.as_view(), name='list-location-fields'),
    path('v1/locationFields/get/list', PipelineListLocationFields.as_view(), name='get-location-fields'),
    path('v1/locationFields/delete/<int:pk>', DeleteLocationFields.as_view(), name='delete-location-fields'),
    path('v1/locationFields/<int:location_id>', RetrieveLocationFields.as_view(), name='retrieve-location-fields'),

    # --------------------------------------------------- MODULES ------------------------------------------------------------------------
    path('v1/groupModule/create', CreateGroupModule.as_view(), name='create-group-module'),
    path('v1/groupModule/update/<int:pk>', UpdateGroupModule.as_view(), name='update-group-module'),
    path('v1/groupModule/retrieve/<int:pk>', RetrieveGroupModule.as_view(), name='retrieve-group-module'),
    path('v1/groupModule/list', GetGroupModule.as_view(), name='list-group-module'),
    path('v1/groupModule/delete/<int:pk>', DeleteGroupModule.as_view(), name='delete-group-module'),
    
    path('v1/userGroupModule/create', CreateUserGroupModule.as_view(), name='create-user-group-module'),
    path('v1/userGroupModule/update/<int:pk>', UpdateUserGroupModule.as_view(), name='create-user-group-module'),
    path('v1/userGroupModule/user/<int:user_id>', ListGroupModuleByUserID.as_view(), name='retrieve-user-group-module'),
    
    #------------------------------------------------------ GROUPS --------------------------------------------------------------------------
    path('v1/group/create', CreateGroup.as_view(), name='create-group'),
    path('v1/group/update/<int:pk>', UpdateGroup.as_view(), name='update-group'),
    path('v1/group/list', GetGroup.as_view(), name='list-group'),
    path('v1/group/<int:pk>', RetrieveGroup.as_view(), name='list-group-by-groupid'),
    path('v1/group/delete/<int:pk>', DeleteGroup.as_view(), name='delete-group'),
    
    #--------------------------------------------------- GROUP FIELDS ---------------------------------------------------------------------------
    path('v1/groupField/create', CreateGroupField.as_view(), name='create-group-field'),
    path('v1/groupField/list', GroupFieldList.as_view(), name='list-group-field'),
    path('v1/groupField/update/<int:pk>', UpdateGroupField.as_view(), name='update-group-field'),
    path('v1/groupField/isHidden/update', UpdateGroupFieldIsHidden.as_view(), name='update-group-field-ishidden'),
    path('v1/groupField/delete/<int:pk>', DeleteGroupField.as_view(), name='delete-group-field'),
    path('v1/groupField/sorting', GroupFieldSorting.as_view(), name='sorting-group-field'),
    
    #--------------------------------------------------- UserGroups -----------------------------------------------------------------------------
    path('v1/userGroup/create', CreateUserGroup.as_view(), name='create-user-group'),
    path('v1/userGroup/update/<int:pk>', UpdateUserGroup.as_view(), name='update-user-group'),
    path('v1/userGroup/update/isPinned/<int:pk>', UpdateUserGroupIsPinned.as_view(), name='update-user-group-is_pinned'),
    path('v1/userGroup/delete/<int:pk>', DestroyUserGroup.as_view(), name='delete-user-group'),
    path('v1/userGroup/<int:user_id>', RetrieveUserGroupByUserID.as_view(), name='retrive-user-group-by-userid'),
    path('v1/userGroup/sorting', UserGroupFieldSorting.as_view(), name='sorting-user-group-by-userid'),

    
    # -----------------------------------------PROJECT PHASE TASK FIELDS URLS--------------------------------------------
    path('v1/project/phase/task/field/create', CreateProjectPhaseTaskFields.as_view(), name = 'project-phase-task-field-create'),
    path('v1/project/phase/task/field/list', GetProjectPhaseTaskFields.as_view(), name = 'project-phase-task-field-list'),
    path('v1/project/phase/task/field/update/<int:pk>', UpdateProjectPhaseTaskFields.as_view(), name = 'project-phase-task-field-update'),
    path('v1/project/phase/task/field/delete/<int:pk>', DeleteProjectPhaseTaskFields.as_view(), name = 'project-phase-task-field-delete'),
    path('v1/project/phase/task/field/retrieve', RetrieveProjectPhaseTaskFields.as_view(), name= 'project-phase-task-field-retrieve'),
    path('v1/project/phase/task/field/<int:task_id>', RetrieveProjectPhaseTaskFieldsByTaskId.as_view(), name= 'project-phase-task-field-retrieve-by-task-id'),
    
    #---------------------------------------------- VIEW(GROUP MODULE) LOCATION FIELDS LOGS---------------------------------------------------------
    path('v1/viewLocationField/logs/<int:group_module_id>', ViewLocationFieldLogsbyModule.as_view(), name = 'group-module-location-field-logs'),
    
    #------------------------------------------------- GROUPVIEWSORTING -----------------------------------------------------------------------
    path('v1/groupView/sorting', GroupViewSorting.as_view(), name='group-view-sorting'),
    path('v1/groupView/list/<int:group_module_id>', GroupViewRetrieve.as_view(), name='group-view-list'),
    path('v1/groupView/create', CreateGroupView.as_view(), name='group-view-create'),
    path('v1/groupView/delete/<int:pk>', GroupViewDelete.as_view(), name='group-view-delete'),
]
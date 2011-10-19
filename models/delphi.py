# coding: utf8

"""
    Delphi decision maker
"""

module = "delphi"
if deployment_settings.has_module(module):

    # Memberships as component of Groups
    s3mgr.model.add_component("delphi_membership",
                              delphi_group="group_id")

    # Problems as component of Groups
    s3mgr.model.add_component("delphi_problem",
                              delphi_group="group_id")

    # Solutions as component of Problems
    s3mgr.model.add_component("delphi_solution",
                              delphi_problem="problem_id")

    # Votes as component of Problems
    #s3mgr.model.add_component("delphi_vote",
    #                          delphi_problem="problem_id")

    # Forum Posts as component of Solutions
    s3mgr.model.add_component("delphi_forum_post",
                              delphi_solution="solution_id")

    def delphi_tables():
        """ Load the Delphi Tables when needed """

        # ---------------------------------------------------------------------
        # Groups
        # ---------------------------------------------------------------------
        tablename = "delphi_group"
        table = db.define_table(tablename,
                                Field("name", notnull=True, unique=True,
                                      label = T("Group Title")),
                                Field("description", "text",
                                      label = T("Description")),
                                Field("active", "boolean", default=True,
                                      label = T("Active")),
                                *s3_meta_fields())

        # CRUD Strings
        ADD_GROUP = T("Add Group")
        LIST_GROUPS = T("List Groups")
        s3.crud_strings[tablename] = Storage(
            title_create = ADD_GROUP,
            title_display = T("Group Details"),
            title_list = LIST_GROUPS,
            title_update = T("Edit Group"),
            title_search = T("Search Groups"),
            subtitle_create = T("Add New Group"),
            subtitle_list = T("Groups"),
            label_list_button = LIST_GROUPS,
            label_create_button = ADD_GROUP,
            label_delete_button = T("Delete Group"),
            msg_record_created = T("Group added"),
            msg_record_modified = T("Group updated"),
            msg_record_deleted = T("Group deleted"),
            msg_list_empty = T("No Groups currently defined"))

        s3mgr.configure(tablename,
                        list_fields=["id",
                                     "name",
                                     "description"])

        def delphi_group_represent(id):
            if not id:
                return NONE
            table = db.delphi_group
            query = (table.id == id)
            record = db(query).select(table.name,
                                      limitby=(0, 1)).first()
            if not record:
                return UNKNOWN_OPT
            return record.name
        
        group_id = S3ReusableField("group_id", db.delphi_group, notnull=True,
                                   label = T("Problem Group"),
                                   requires = IS_ONE_OF(db, "delphi_group.id",
                                                        "%(name)s"),
                                   represent = delphi_group_represent)

        user_id = S3ReusableField("user_id", db.auth_user, notnull=True,
                                  label = T("User"),
                                  requires = IS_ONE_OF(db, "auth_user.id",
                                                       s3_user_represent),
                                  represent = s3_user_represent)

        # ---------------------------------------------------------------------
        # Group Membership
        # ---------------------------------------------------------------------
        delphi_role_opts = {
            1:T("Guest"),
            2:T("Contributor"),
            3:T("Participant"),
            4:T("Moderator")
        }
        tablename = "delphi_membership"
        table = db.define_table(tablename,
                                group_id(),
                                user_id(),
                                Field("description",
                                      label = T("Description")),
                                # @ToDo: Change how Membership Requests work
                                Field("req", "boolean", default=False,
                                      label = T("Request")), # Membership Request
                                Field("status", "integer", default=1,
                                      label = T("Status"),
                                      requires = IS_IN_SET(delphi_role_opts,
                                                           zero=None),
                                      represent = lambda opt: \
                                        delphi_role_opts.get(opt, UNKNOWN_OPT),
                                      comment = DIV( _class="tooltip",
                                                     _title="%s|%s|%s|%s|%s" % (T("Status"),
                                                                                T("Guests can view all details"),
                                                                                T("A Contributor can additionally Post comments to the proposed Solutions & add alternative Solutions"),
                                                                                T("A Participant can additionally Vote"),
                                                                                T("A Moderator can additionally create Problems & control Memberships")))
                                        ),
                                *s3_meta_fields()
                                )

        # CRUD Strings
        ADD_MEMBERSHIP = T("Add Membership")
        LIST_MEMBERSHIPS = T("List Memberships")
        s3.crud_strings[tablename] = Storage(
            title_create = ADD_MEMBERSHIP,
            title_display = T("Membership Details"),
            title_list = LIST_MEMBERSHIPS,
            title_update = T("Edit Membership"),
            title_search = T("Search Memberships"),
            subtitle_create = T("Add New Membership"),
            subtitle_list = T("Memberships"),
            label_list_button = LIST_MEMBERSHIPS,
            label_create_button = ADD_MEMBERSHIP,
            label_delete_button = T("Remove Membership"),
            msg_record_created = T("Membership added"),
            msg_record_modified = T("Membership updated"),
            msg_record_deleted = T("Membership deleted"),
            msg_list_empty = T("No Memberships currently defined"))

        s3mgr.configure(tablename,
                        list_fields=["id",
                                     "group_id",
                                     "user_id",
                                     "status",
                                     "req"])

        # ---------------------------------------------------------------------
        # Problems
        # ---------------------------------------------------------------------
        tablename = "delphi_problem"
        table = db.define_table(tablename,
                                group_id(),
                                Field("name", notnull=True, unique=True,
                                      label = T("Problem Title")),
                                Field("description", "text",
                                      label = T("Description")),
                                Field("criteria", "text", notnull=True,
                                      label = T("Criteria")),
                                Field("active", "boolean", default=True,
                                      label = T("Active")),
                                *s3_meta_fields()
                                )

        table.modified_on.label = T("Last Modification")

        # CRUD Strings
        ADD_PROBLEM = T("Add Problem")
        LIST_PROBLEMS = T("List Problems")
        s3.crud_strings[tablename] = Storage(
            title_create = ADD_PROBLEM,
            title_display = T("Problem Details"),
            title_list = LIST_PROBLEMS,
            title_update = T("Edit Problem"),
            title_search = T("Search Problems"),
            subtitle_create = T("Add New Problem"),
            subtitle_list = T("Problems"),
            label_list_button = LIST_PROBLEMS,
            label_create_button = ADD_PROBLEM,
            label_delete_button = T("Delete Problem"),
            msg_record_created = T("Problem added"),
            msg_record_modified = T("Problem updated"),
            msg_record_deleted = T("Problem deleted"),
            msg_list_empty = T("No Problems currently defined"))

        s3mgr.configure(tablename,
                        list_fields=["id",
                                     "group_id",
                                     "name",
                                     "created_by",
                                     "modified_on"])

        def delphi_problem_represent(id):
            if not id:
                return NONE
            table = db.delphi_problem
            query = (table.id == id)
            record = db(query).select(table.name,
                                      limitby=(0, 1)).first()
            if not record:
                return UNKNOWN_OPT
            return record.name
        
        problem_id = S3ReusableField("problem_id", db.delphi_problem, notnull=True,
                                     label = T("Problem"),
                                     requires = IS_ONE_OF(db, "delphi_problem.id",
                                                          "%(name)s"),
                                     represent = delphi_problem_represent)

        # ---------------------------------------------------------------------
        # Solutions
        # ---------------------------------------------------------------------
        tablename = "delphi_solution"
        table = db.define_table(tablename,
                                problem_id(),
                                Field("name",
                                      label = T("Title"),
                                      requires = IS_NOT_EMPTY()),
                                Field("description", "text",
                                      label = T("Description")),
                                *s3_meta_fields()
                                )

        table.created_by.label = T("Suggested By")
        table.modified_on.label = T("Last Modification")

        # CRUD Strings
        ADD_SOLUTION = T("Add Solution")
        LIST_SOLUTIONS = T("List Solutions")
        s3.crud_strings[tablename] = Storage(
            title_create = ADD_SOLUTION,
            title_display = T("Solution Details"),
            title_list = LIST_SOLUTIONS,
            title_update = T("Edit Solution"),
            title_search = T("Search Solutions"),
            subtitle_create = T("Add New Solution"),
            subtitle_list = T("Solutions"),
            label_list_button = LIST_SOLUTIONS,
            label_create_button = ADD_SOLUTION,
            label_delete_button = T("Delete Solution"),
            msg_record_created = T("Solution added"),
            msg_record_modified = T("Solution updated"),
            msg_record_deleted = T("Solution deleted"),
            msg_list_empty = T("No Solutions currently defined"))

        s3mgr.configure(tablename,
                        list_fields=["id",
                                     "problem_id",
                                     "name",
                                     "created_by",
                                     "modified_on"])

        def delphi_solution_represent(id):
            if not id:
                return NONE
            table = db.delphi_solution
            query = (table.id == id)
            record = db(query).select(table.name,
                                      limitby=(0, 1)).first()
            if not record:
                return UNKNOWN_OPT
            return record.name
        
        solution_id = S3ReusableField("solution_id", db.delphi_solution, notnull=True,
                                      label = T("Solution"),
                                      requires = IS_ONE_OF(db, "delphi_solution.id",
                                                           "%(name)s"),
                                      represent = delphi_solution_represent)

        # ---------------------------------------------------------------------
        # Votes
        # ---------------------------------------------------------------------
        tablename = "delphi_vote"
        table = db.define_table(tablename,
                                problem_id(),
                                solution_id(),
                                Field("rank", "integer",
                                      label = T("Rank")),
                                # @ToDo: Replace by created_by
                                Field("user_id", db.auth_user, writable=False, readable=False),
                                *s3_meta_fields()
                                )

        table.user_id.label = T("User")
        table.user_id.default = auth.user.id if auth.user else 0

        # CRUD Strings
        ADD_VOTE = T("Add Vote")
        LIST_VOTES = T("List Votes")
        s3.crud_strings[tablename] = Storage(
            title_create = ADD_VOTE,
            title_display = T("Vote Details"),
            title_list = LIST_VOTES,
            title_update = T("Edit Vote"),
            title_search = T("Search Votes"),
            subtitle_create = T("Add New Vote"),
            subtitle_list = T("Votes"),
            label_list_button = LIST_VOTES,
            label_create_button = ADD_VOTE,
            label_delete_button = T("Delete Vote"),
            msg_record_created = T("Vote added"),
            msg_record_modified = T("Vote updated"),
            msg_record_deleted = T("Vote deleted"),
            msg_list_empty = T("No Votes currently defined"))

        # ---------------------------------------------------------------------
        # Comments
        # ---------------------------------------------------------------------
        tablename = "delphi_comment"
        table = db.define_table(tablename,
                                solution_id(),
                                Field("title",
                                      label = T("Title")),
                                Field("body", "text", notnull=True,
                                      label = T("Comment")),
                                *s3_meta_fields()
                                )
        
        # ---------------------------------------------------------------------
        # Forum Posts
        # @ToDo: Attachments
        # @ToDo: Rich Text Editor
        # ---------------------------------------------------------------------
        tablename = "delphi_forum_post"
        table = db.define_table(tablename,
                                solution_id(),
                                Field("title",
                                      label = T("Title")),
                                Field("post", "text", notnull=True,
                                      label = T("Post")),
                                Field("post_html", "text", default="",
                                      label = T("Post HTML")),
                                # @ToDo: Replace by created_by
                                #Field("user_id", db.auth_user, writable=False, readable=False),
                                *s3_meta_fields()
                                )

        #table.user_id.label = T("User")
        #table.user_id.default = auth.user.id if auth.user else 0

        # @ToDo: Allow Anonymous Posts
        table.created_by.label = T("Posted By")
        table.modified_on.label = T("Last Modification")

        # CRUD Strings
        ADD_POST = T("Add Post")
        LIST_POSTS = T("List Posts")
        s3.crud_strings[tablename] = Storage(
            title_create = ADD_POST,
            title_display = T("Post Details"),
            title_list = LIST_POSTS,
            title_update = T("Edit Post"),
            title_search = T("Search Posts"),
            subtitle_create = T("Add New Post"),
            subtitle_list = T("Posts"),
            label_list_button = LIST_POSTS,
            label_create_button = ADD_POST,
            label_delete_button = T("Delete Post"),
            msg_record_created = T("Post added"),
            msg_record_modified = T("Post updated"),
            msg_record_deleted = T("Post deleted"),
            msg_list_empty = T("No Posts yet made"))

        s3mgr.configure(tablename,
                        list_fields=["id",
                                     "solution_id",
                                     "title",
                                     "post",
                                     "created_by",
                                     "modified_on"])

        # =====================================================================
        # Pass variables back to global scope (response.s3.*)
        return dict (
            )

    # Provide a handle to this load function
    s3mgr.loader(delphi_tables,
                 "delphi_group",
                 "delphi_membership",
                 "delphi_problem",
                 "delphi_solution",
                 "delphi_vote",
                 "delphi_forum_post"
                 )

# END =========================================================================

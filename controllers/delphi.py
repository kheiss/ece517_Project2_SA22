# coding: utf8

"""
    Delphi Decision Maker - Controllers
"""

module = request.controller
resourcename = request.function

if module not in deployment_settings.modules:
    raise HTTP(404, body="Module disabled: %s" % module)

# Load Models
s3mgr.load("delphi_group")

s3_menu(module)

# -----------------------------------------------------------------------------
UNIT_NORMAL = (
    ( 0.0, .0, .01, .02, .03, .04, .05, .06, .07, .08, .09 ),
    ( .0, .5000, .5040, .5080, .5120, .5160, .5199, .5239, .5279, .5319, .5359 ),
    ( .1, .5398, .5438, .5478, .5517, .5557, .5596, .5636, .5675, .5714, .5753 ),
    ( .2, .5793, .5832, .5871, .5910, .5948, .5987, .6026, .6064, .6103, .6141 ),
    ( .3, .6179, .6217, .6255, .6293, .6331, .6368, .6406, .6443, .6480, .6517 ),
    ( .4, .6554, .6591, .6628, .6664, .6700, .6736, .6772, .6808, .6844, .6879 ),

    ( .5, .6915, .6950, .6985, .7019, .7054, .7088, .7123, .7157, .7190, .7224 ),
    ( .6, .7257, .7291, .7324, .7357, .7389, .7422, .7454, .7486, .7517, .7549 ),
    ( .7, .7580, .7611, .7642, .7673, .7703, .7734, .7764, .7794, .7823, .7852 ),
    ( .8, .7881, .7910, .7939, .7967, .7995, .8023, .8051, .8078, .8106, .8133 ),
    ( .9, .8159, .8186, .8212, .8238, .8264, .8289, .8315, .8340, .8365, .8389 ),

    ( 1.0, .8415, .8438, .8461, .8485, .8508, .8531, .8554, .8577, .8509, .8621 ),
    ( 1.1, .8643, .8665, .8686, .8708, .8729, .8749, .8770, .8790, .8810, .8830 ),
    ( 1.2, .8849, .8869, .8888, .8907, .8925, .8944, .8962, .8980, .8997, .90147 ),
    ( 1.3, .90320, .90490, .90658, .90824, .90988, .91149, .91309, .91466, .91621, .91774 ),
    ( 1.4, .91924, .92073, .92220, .92364, .92507, .92647, .92785, .92922, .93056, .93189 ),

    ( 1.5, .93319, .93448, .93574, .93699, .93822, .93943, .94062, .94179, .94295, .94408 ),
    ( 1.6, .94520, .94630, .94738, .94845, .94950, .95053, .95154, .95254, .95352, .95449 ),
    ( 1.7, .95543, .95637, .95728, .95818, .95907, .95994, .96080, .96164, .96246, .96327 ),
    ( 1.8, .96407, .96485, .96562, .96638, .96712, .96784, .97856, .96926, .96995, .97062 ),
    ( 1.9, .97128, .97193, .97257, .97320, .97381, .97441, .97500, .97558, .97615, .97670 ),

    ( 2.0, .97725, .97778, .97831, .97882, .97932, .97982, .98030, .98077, .98124, .98169 ),
    ( 2.1, .98214, .98257, .98300, .98341, .98382, .98422, .98461, .98500, .98537, .98574 ),
    ( 2.2, .98610, .98645, .98679, .98713, .98745, .98778, .98809, .98840, .98870, .98899 ),
    ( 2.3, .98928, .98956, .98983, .990097, .990358, .990613, .990863, .991106, .991344, .991576 ),
    ( 2.4, .991802, .992024, .992240, .992451, .992656, .992857, .993053, .993244, .993431, .993613 ),

    ( 2.5, .993790, .993963, .994132, .994297, .994457, .994614, .994766, .994915, .995060, .995201 ),
    ( 2.6, .995339, .995473, .995604, .995731, .995855, .995975, .996093, .996207, .996319, .996427 ),
    ( 2.7, .996533, .996636, .996736, .996833, .996928, .997020, .997110, .997197, .997282, .997365 ),
    ( 2.8, .997445, .997523, .997599, .997673, .997744, .997814, .997882, .997948, .998012, .998074 ),
    ( 2.9, .998134, .998193, .998250, .998305, .998359, .998411, .998460, .998511, .998559, .998605 ),

    ( 3.0, .998650, .998694, .998736, .998777, .998817, .998856, .998893, .998930, .998965, .998999 ),
    ( 3.1, .9990324, .9990646, .9990957, .9991260, .9991553, .9991836, .9992112, .9992378, .9992636, .9992886 ),
    ( 3.2, .9993129, .9993363, .9993590, .9993810, .9994024, .9994230, .9994429, .9994623, .9994810, .9994991 ),
    ( 3.3, .9995166, .9995335, .9995499, .9995658, .9995811, .9995959, .9996103, .9996242, .9996376, .9996505 ),
    ( 3.4, .9996631, .9996752, .9996869, .9996982, .9997091, .9997197, .9997299, .9997398, .9997493, .9997585 ),

    ( 3.5, .9997674, .9997759, .9997842, .9997922, .9997999, .9998074, .9998146, .9998215, .9998282, .9998347 ),
    ( 3.6, .9998409, .9998469, .9998527, .9998583, .9998637, .9998689, .9998739, .9998787, .9998834, .9998879 ),
    ( 3.7, .9998922, .9998964, .99990039, .99990426, .99990799, .99991158, .99991504, .99991838, .99992159, .99992468 ),
    ( 3.8, .99992765, .99993052, .99993327, .99993593, .99993848, .99994094, .99994331, .99994558, .99994777, .99994988 ),
    ( 3.9, .99995190, .99995385, .99995573, .99995753, .99995926, .99996092, .99996253, .99996406, .99996554, .99996696 ),

    ( 4.0, .99996833, .99996964, .99997090, .99997211, .99997327, .99997439, .99997546, .99997649, .99997748, .99997843 ),
    ( 4.1, .99997934, .99998022, .99998106, .99998186, .99998263, .99998338, .99998409, .99998477, .99998542, .99998605 ),
    ( 4.2, .99998665, .99998723, .99998778, .99998832, .99998882, .99998931, .99998978, .999990226, .999990655, .999991066 ),
    ( 4.3, .999991460, .999991837, .999992199, .999992545, .999992876, .999993193, .999993497, .999993788, .999994066, .999994332 ),
    ( 4.4, .999994587, .999994831, .999995065, .999995288, .999995502, .999995706, .999995902, .999996089, .999996268, .999996439 ),

    ( 4.5, .999996602, .999996759, .999996908, .999997051, .999997187, .999997318, .999997442, .999997561, .999997675, .999997784 ),
    ( 4.6, .999997888, .999997987, .999998081, .999998172, .999998258, .999998340, .999998419, .999998494, .999998566, .999998634 ),
    ( 4.7, .999998699, .999998761, .999998821, .999998877, .999998931, .999998983, .9999990320, .9999990789, .9999991235, .9999991661 ),
    ( 4.8, .9999992067, .9999992453, .9999992822, .9999993173, .9999993508, .9999993827, .9999994131, .9999994420, .9999994696, .9999994958 ),
    ( 4.9, .9999995208, .9999995446, .9999995673, .9999995889, .9999996094, .9999996289, .9999996475, .9999996652, .9999996821, .9999996981 )
)
MIN_COLOR = (0xfc, 0xaf, 0x3e)
MAX_COLOR = (0x4e, 0x9a, 0x06)

# -----------------------------------------------------------------------------
class DU:
    """ Delphi User class """
    
    def user(self):
        # Used by Discuss() (& summary())
        return db.auth_user[self.user_id]

    def __init__(self, group_id=None):
        self.user_id = auth.user.id if (auth.is_logged_in() and session.auth) else None
        self.status = "guest"
        self.membership = None
        if s3_has_role("DelphiAdmin"):
            # DelphiAdmin is Moderator for every Group
            self.status = "moderator"
        elif self.user_id != None and group_id != None:
            table = db.delphi_membership
            query = (table.group_id == group_id) & \
                    (table.user_id == self.user_id)
            self.membership = db(query).select()
            if self.membership:
                self.membership = self.membership[0]
                self.status = self.membership.status

        self.authorised = (self.status == "moderator")

        self.can_vote = self.status in ("moderator", "participant")
        self.can_add_item = self.status != "guest"
        self.can_post = self.status != "guest"


# -----------------------------------------------------------------------------
def __lookupTable(mp):
    """ Utility function used by Scale of Results """

    unitValue = 0.0

    for j in range(1, 50):
        if mp == UNIT_NORMAL[j][1]:
            unitValue = UNIT_NORMAL[j][0]
        elif (UNIT_NORMAL[j][1] < mp) and (mp < UNIT_NORMAL[j + 1][1]):
            for i in range(2, 11):
                if (UNIT_NORMAL[j][i - 1] < mp) and (mp <= UNIT_NORMAL[j][i]):
                    unitValue = UNIT_NORMAL[j][0] + UNIT_NORMAL[0][i]
            if mp > UNIT_NORMAL[j][10]:
                unitValue = UNIT_NORMAL[j + 1][0]

    if (mp > UNIT_NORMAL[50][1]) and (mp < UNIT_NORMAL[50][10]):
        for i in range(2, 11):
            if (UNIT_NORMAL[50][i - 1] < mp) and (mp <= UNIT_NORMAL[50][i]):
                unitValue = UNIT_NORMAL[50][0] + UNIT_NORMAL[0][i]

    if mp > UNIT_NORMAL[50][10]:
        unitValue = 5.0 # suppose infinite value occur

    return unitValue


# -----------------------------------------------------------------------------
def __cal_votes(pr, i_ids):
    """ Utility function used by Vote & Scale of Results """
    num_voted = 0
    votes = {}
    for i1 in i_ids:
        for i2 in i_ids:
            votes[(i1, i2)] = 0

    users = db(db.auth_user.id > 0).select()

    table = db.delphi_vote
    for u in users:
        query = (table.problem_id == pr.id) & \
                (table.user_id == u.id) & \
                (table.rank < 9888)

        records = db(query).select(table.solution_id,
                                   table.rank,
                                   orderby = table.rank)
        u_votes = [v.solution_id for v in records]

        if len(u_votes) > 1: num_voted += 1
        for i1 in range(len(u_votes)):
            for i2 in range(i1+1, len(u_votes)):
                votes[(u_votes[i1], u_votes[i2])] += 1

    return (votes, num_voted)


# -----------------------------------------------------------------------------
def __lookup_problem_and_user(solution=None):
    """
        Lookup the Problem & the User
        - used by Discuss() (& summary())
    """

    if solution:
        problem_id = solution.problem_id
    else:
        problem_id = request.args[0]

    problem = db.delphi_problem[problem_id]
    if not problem:
        raise HTTP(404)

    # Get this User's permissions for this Group
    user = DU(problem.group_id)

    return (problem, user)


# =============================================================================
def index():
    """
        Module Home Page
        - provide the list of currently-Active Problems
    """

    # Simply direct to the Problems REST controller
    redirect(URL(f="problem"))

    module_name = deployment_settings.modules[module].name_nice

    groups = db(db.delphi_group.active == True).select()
    result = []
    for group in groups:
        actions = []
        duser = DU(group)
        if duser.authorised:
            actions.append(("group/%d/update" % group.id, T("Edit")))
            actions.append(("new_problem/create/?group=%s&next=%s" % \
                    (group.id,
                    URL(f="group_summary", args=group.id)),
                    "Add New Problem"))
            actions.append(("group_summary/%s/#request" % group.id, T("Review Requests")))
        else:
            actions.append(("group_summary/%s/#request" % group.id,
                    "Role: %s%s" % (duser.status,
                                    (duser.membership and duser.membership.req) and "*" or "")))

        table = db.delphi_problem
        query = (table.group_id == group.id) & \
                (table.active == True)
        latest_problems = db(query).select(orderby =~ table.modified_on)
        result.append((group, latest_problems, actions))

    response.title = module_name
    return dict(groups_problems=result,
                name=T("Active Problems"),
                module_name=module_name)

# =============================================================================
def group_rheader(r, tabs = []):
    """ Group rheader """

    if r.representation == "html":
        if r.record is None:
            # List or Create form: rheader makes no sense here
            return None
        
        tabs = [
                (T("Basic Details"), None),
                (T("Problems"), "problem"),
               ]
        # @ToDo: Check for Group Moderators too
        if s3_has_role("DelphiAdmin"):
            tabs.append((T("Membership"), "membership"))
        
        rheader_tabs = s3_rheader_tabs(r, tabs)

        group = r.record

        rheader = DIV(TABLE(
            TR(
                TH("%s: " % T("Group")),
                group.name,
                ),
            TR(
                TH("%s: " % T("Description")),
                group.description,
                ),
            TR(
                TH("%s: " % T("Active")),
                group.active,
                ),
            ),
            rheader_tabs
        )
        return rheader
    return None
    
# -----------------------------------------------------------------------------
def group():
    """ Problem Group REST Controller """

    #if not s3_has_role("DelphiAdmin"):
    #    auth.permission.fail()

    def prep(r):
        if r.interactive:
            if r.component:
                tablename = r.component.tablename
                list_fields = s3mgr.model.get_config(tablename, 
                                                     "list_fields")
                try:
                    list_fields.remove("group_id")
                except:
                    pass
                s3mgr.configure(tablename,
                                list_fields=list_fields)
        return True
    response.s3.prep = prep

    rheader = group_rheader
    return s3_rest_controller(module, resourcename,
                              rheader=rheader)

# =============================================================================
def problem_rheader(r, tabs = []):
    """ Problem rheader """
    
    if r.representation == "html":
        if r.record is None:
            # List or Create form: rheader makes no sense here
            return None
        
        problem = r.record

        tabs = [
                # Components
                (T("Solutions"), "solution"),
                # Custom Methods
                (T("Vote"), "vote"),
                (T("Scale of Results"), "results"),
               ]
        # @ToDo: Replace this by Group Moderator
        if s3_has_role("DelphiAdmin"):
            tabs.append((T("Edit"), None))
        
        rheader_tabs = s3_rheader_tabs(r, tabs)

        rheader = DIV(TABLE(
            TR(
                TH("%s: " % T("Problem")),
                problem.name,
                ),
            TR(
                TH("%s: " % T("Description")),
                problem.description,
                ),
            TR(
                TH("%s: " % T("Criteria")),
                problem.criteria,
                ),
            TR(
                TH("%s: " % T("Active")),
                problem.active,
                ),
            ),
            rheader_tabs
        )
        return rheader
    return None
    
# -----------------------------------------------------------------------------
def vote(r, **attr):
    """
        Custom Method to allow Voting on Solutions to a Problem
    """

    problem = r.record
    
    # Get this User's permissions for this Group
    duser = DU(problem.group_id)

    # Add the RHeader to maintain consistency with the other pages
    rheader = problem_rheader(r)
    
    # Lookup Solutions
    items = dict([(i.id, i.name) for i in problem.delphi_solution.select()])
    n = len(items)

    if duser.user_id:
        table = db.delphi_vote
        query = (table.problem_id == problem.id) & \
                (table.user_id == duser.user_id)
        voted = db(query).select(orderby = table.rank)
    else:
        voted = False

    # v.rank == 9999 -> user has selected not to vote on v.solution_id
    #   rank == 9998 -> the solution is new and the user hasn't voted on it yet
    if voted:
        sorted_items = [v.solution_id for v in voted]
        ranks = dict([(v.solution_id, v.rank) for v in voted])
        n = len(sorted_items)
        last_enabled = -1
        while ((-last_enabled) <= n) and (ranks[sorted_items[last_enabled]] == 9999):
            last_enabled -= 1
        for i in items.keys():
            if not i in ranks.keys():
                if last_enabled == -1:
                    sorted_items.append(i)
                else:
                    sorted_items.insert(last_enabled + 1, i)
                ranks[i] = 9998
    else:
        votes, num_voted = __cal_votes(problem, items.keys())
        def cc1(i1, i2):
            if votes[(i1, i2)] > votes[(i2, i1)]: return -1
            if votes[(i1, i2)] < votes[(i2, i1)]: return +1
            return 0
        sorted_items = sorted(list(items.keys()), cc1)
        ranks = dict([(i, 9998) for i in sorted_items])

    # Add Custom CSS from Static (cacheable)
    response.s3.stylesheets.append("S3/delphi_vote.css")

    # Add Custom Javascript
    can_vote = "true" if duser.can_vote else "false"
    _voted = "true" if voted else "false"
    _sorted_items = json.dumps(sorted_items)
    _items = json.dumps(items)
    _ranks = json.dumps(ranks)

    # Settings to be picked up by Static code
    js = "".join(("""
var problem_id = """, str(problem.id), """;
var can_vote = """, can_vote, """;
var voted = """, _voted, """;
var sorted_items = """, _sorted_items, """;
var items = """, _items, """;
var ranks = """, _ranks, """;
S3.i18n.delphi_ignore = '""", str(T("ignore")), """';
S3.i18n.delphi_consider = '""", str(T("consider")), """';
S3.i18n.delphi_saved = '""", str(T("Saved.")), """';
S3.i18n.delphi_update_list = '""", str(T("Update your current ordered list")), """';
S3.i18n.delphi_failed = '""", str(T("Failed!")), """';
S3.i18n.delphi_saving = '""", str(T("Saving...")), """';
S3.i18n.delphi_saved = '""", str(T("Saved.")), """';
"""))
    response.s3.js_global.append(js)

    # Static code which can be cached
    response.s3.scripts.append(URL(c="static", f="scripts",
                                   args=["S3", "s3.delphi.js"]))

    response.s3.jquery_ready.append("""
fill_vote_items();
$('#vote_button').click(function() {
    $(this).hide();
    $('#vote_items').hide();
    quicksort_init();
});
$('#comp_tr').hide();""")

    response.view = "delphi/vote.html"
    return dict(rheader=rheader,
                duser=duser,
                voted=voted)

# -----------------------------------------------------------------------------
def save_vote():
    """ Function accessed by AJAX from vote() to save the results of a Vote """

    problem_id = request.args(0)
    if not problem_id:
        raise HTTP(400)

    problem = db.delphi_problem[problem_id]
    if not problem:
        raise HTTP(404)

    # Get this User's permissions for this Group
    duser = DU(problem.group_id)

    if not duser.can_vote:
        auth.permission.fail()

    items = [i.id for i in problem.delphi_solution.select()]
    ranks = {}
    for item_id in items:
        if str(item_id) in request.post_vars:
            ranks[item_id] = request.post_vars[str(item_id)]

    table = db.delphi_vote
    query = (table.problem_id == problem.id) & \
            (table.user_id == duser.user_id)
    if duser.user_id:
        voted = db(query).select(orderby = table.rank)
    else:
        voted = False

    if voted:
        for old in voted:
            del table[old.id]

    for item_id, rank in ranks.items():
         table.insert(problem_id=problem.id, solution_id=item_id, rank=rank)

    return '"OK"'

# -----------------------------------------------------------------------------
def results(r, **attr):
    """
        Custom Method to show the Scale of Results
    """

    problem = r.record
    
    # Get this User's permissions for this Group
    duser = DU(problem.group_id)

    response.view = "delphi/results.html"

    # Add the RHeader to maintain consistency with the other pages
    rheader = problem_rheader(r)
    
    # Lookup Solutions
    items = dict([(i.id, i.name) for i in problem.delphi_solution.select()])
    i_ids = items.keys()
    n = len(i_ids)

    empty = dict(items=items,
                 beans=[],
                 duser=duser,
                 votes={},
                 scale={},
                 num_voted=0)

    if n == 0:
        return empty

    votes, num_voted = __cal_votes(problem, i_ids)

    scale = {}

    if num_voted == 0:
        return empty

    for i1 in i_ids:
        scale[i1] = 0
        for i2 in i_ids:
            if i1 == i2:
                continue
            tt2 = float(votes[(i1, i2)] + votes[(i2, i1)])
            if votes[(i1, i2)] > votes[(i2, i1)]:
                scale[i1] += __lookupTable(votes[(i1, i2)] / tt2)
            elif votes[(i1, i2)] < votes[(i2, i1)]:
                scale[i1] -= __lookupTable(votes[(i2, i1)] / tt2)

    def cc2(i1, i2):
        if scale[i1] > scale[i2]:
            return -1
        if scale[i1] < scale[i2]:
            return +1
        return 0

    i_ids.sort(cc2)

    beans_num = int((n+1) * 2)
    bean_size = 10.0 * n / beans_num
    beans = []
    i = 0
    for j in range(beans_num):
        color = "%02x%02x%02x" % \
            tuple([int(((j*MIN_COLOR[k]) + ((beans_num-j)*MAX_COLOR[k])) / beans_num) for k in (0, 1, 2)])
        limit = ((beans_num - j - 1) * bean_size) - (5 * n)
        bean = []
        while i < n and scale[i_ids[i]] >= limit:
            bean.append(i_ids[i])
            i += 1
        beans.append((color, bean))

    return dict(rheader=rheader,
                duser=duser,
                items=items,
                beans=beans,
                scale=scale,
                votes=votes,
                num_voted=num_voted)

# -----------------------------------------------------------------------------
def problem():
    """ Problem REST Controller """

    tablename = "%s_%s" % (module, resourcename)
    table = db[tablename]

    # Custom Methods
    s3mgr.model.set_method(module, resourcename,
                           method="vote",
                           action=vote)

    s3mgr.model.set_method(module, resourcename,
                           method="results",
                           action=results)

    # Filter to just Active Problems
    response.s3.filter = (table.active == True)
    
    # @ToDo: Check for Group Moderators too
    if not s3_has_role("DelphiAdmin"):
        # Remove ability to create new Problems
        s3mgr.configure(tablename,
                        insertable=False)

    def prep(r):
        if r.interactive:
            if r.component and r.component_name == "solution":
                tablename = r.component.tablename
                list_fields = s3mgr.model.get_config(tablename, 
                                                     "list_fields")
                try:
                    list_fields.remove("problem_id")
                except:
                    pass
                s3mgr.configure(tablename,
                                list_fields=list_fields)
        return True
    response.s3.prep = prep

    def postp(r, output):
        if r.interactive:
            if not r.component:
                response.s3.actions = [
                        dict(label=str(T("Solutions")),
                             _class="action-btn",
                             url=URL(args=["[id]", "solution"])),
                        dict(label=str(T("Vote")),
                             _class="action-btn",
                             url=URL(f="vote",
                                     args=["[id]"])),
                    ]
            elif r.component_name == "solution":
                response.s3.actions = [
                        dict(label=str(T("Discussion")),
                             _class="action-btn",
                             url=URL(f="solution",
                                     args=["[id]", "discuss"])),
                    ]
        return output
    response.s3.postp = postp

    rheader = problem_rheader
    return s3_rest_controller(module, resourcename,
                              rheader=rheader)

# =============================================================================
def solution_rheader(r, tabs = []):
    """ Solution rheader """

    if r.representation == "html":
        if r.record is None:
            # List or Create form: rheader makes no sense here
            return None
        
        tabs = [
                #(T("Discussion"), "forum_post"),
                (T("Discussion"), "discuss"),
               ]
        
        # @ToDo: Replace this by Group Moderator &/or Owner of the Solution
        # (although should owner be allowed to edit after Voting?)
        if s3_has_role("DelphiAdmin"):
            tabs.append((T("Edit"), None))

        rheader_tabs = s3_rheader_tabs(r, tabs)

        solution = r.record

        rheader = DIV(TABLE(
            TR(
                TH("%s: " % T("Solution")),
                solution.name,
                ),
            TR(
                TH("%s: " % T("Description")),
                solution.description,
                ),
            TR(
                TH("%s: " % T("Suggested By")),
                s3_user_represent(solution.created_by),
                ),
            TR(
                TH("%s: " % T("Last Modification")),
                solution.modified_on,
                ),
            ),
            rheader_tabs
        )
        return rheader
    return None
    
# -----------------------------------------------------------------------------
def discuss(r, **attr):
    """ Custom Method to manage the discussion of a proposed Solution """

    # Add the RHeader to maintain consistency with the other pages
    rheader = solution_rheader(r)

    solution_id = r.id
    response.view = "delphi/discuss.html"
    return dict(rheader=rheader,
                solution_id=solution_id)

# -----------------------------------------------------------------------------
def comments():
    """ Function accessed by AJAX from discuss() to handle Comments """

    solution_id = request.args(0)
    if not solution_id:
        raise HTTP(400)

    # Form to add a new Comment
    table = db.delphi_comment
    table.solution_id.default = solution_id
    table.solution_id.writable = table.solution_id.readable = False
    form=crud.create(table)

    # List of existing Comments
    comments = db(table.solution_id == solution_id).select()

    return dict(form=form,
                comments=comments)

# -----------------------------------------------------------------------------
def solution():
    """ Solution REST Controller """

    # @ToDo: Permissions check for policy 1?

    # Creating Solutions is done via the Component Tab
    tablename = "%s_%s" % (module, resourcename)
    s3mgr.configure(tablename,
                    insertable=False)

    # Custom Methods
    s3mgr.model.set_method(module, resourcename,
                           method="discuss",
                           action=discuss)

    def prep(r):
        if r.interactive:
            if r.component:
                tablename = r.component.tablename
                list_fields = s3mgr.model.get_config(tablename, 
                                                     "list_fields")
                try:
                    list_fields.remove("solution_id")
                except:
                    pass
                s3mgr.configure(tablename,
                                list_fields=list_fields)
            else:
                r.table.problem_id.writable = False
        return True
    response.s3.prep = prep

    def postp(r, output):
        if r.interactive:
            if not r.component:
                response.s3.actions = [
                        dict(label=str(T("Discussion")),
                             _class="action-btn",
                             url=URL(args=["[id]", "discuss"])),
                    ]
        return output
    response.s3.postp = postp

    rheader = solution_rheader
    return s3_rest_controller(module, resourcename,
                              rheader=rheader)

# =============================================================================
# Deprecated Functions
# =============================================================================
def summary():
    """
        Dashboard for Problems
        @deprecated - replaced by Problem page + Component Tabs
    """

    problem, duser = __lookup_problem_and_user()
    user = duser.user()
    if user:
        voted = user.delphi_vote.select()
    else:
        voted = False

    if duser.can_add_item and "item_name" in request.post_vars:
        db.delphi_solution.insert(problem_id=problem,
                                  name=request.post_vars["item_name"],
                                  description=request.post_vars["item_description"])

    return dict(problem=problem,
                items=problem.delphi_solution.select(),
                voted=voted,
                name=T("Options"),
                duser=duser)

# -----------------------------------------------------------------------------
def group_summary():
    """
        Dashboard for Groups
        @deprecated - replaced by Group page + Component Tabs

        @ToDo: Handle User Requests
    """
    group_id = request.args(0)
    if not group_id:
        raise HTTP(400)
    group = db.delphi_group[group_id]
    if not group:
        raise HTTP(404)

    duser = DU(group.id)

    forms = []
    table = db.delphi_membership
    table.req.default = True
    table.user_id.writable = False
    table.user_id.default = duser.user_id
    table.group_id.default = group_id
    table.group_id.writable = False
    fields = ["user_id", "description", "status"]

    if duser.authorised:
        fields.append("req")
        query = (table.group_id == group.id) & \
                (table.req == True)
        membership_requests = db(query).select()
        for membership_req in membership_requests:
            form = SQLFORM(table,
                           record=membership_req.id,
                           fields=fields,
                           labels={"req": "%s:" % T("Needs more review")})
            ret = form.accepts(request.post_vars, session, dbio=True)
            if form.errors:
                session.error = T("There are errors")

            forms.append(form)

    elif duser.user_id:
        table.status.writable = False
        if duser.membership:
            fields.append("req")
        form = SQLFORM(table,
                       record=duser.membership,
                       fields=fields,
                       labels={
                            "status": "%s:" % T("Current status"),
                            "req": "%s:" % T("Request for review")
                            })
        ret = form.accepts(request.post_vars, session, dbio=True)
        if form.errors:
            session.error = T("There are errors")

        forms.append(form)

    table = db.delphi_problem
    query = (table.group_id == group.id) & \
            (table.active == True)
    latest_problems = db(query).select(orderby =~ table.modified_on)

    return dict(latest_problems=latest_problems,
                group=group,
                duser=duser,
                name=T("Active Problems in %(group_name)s") % \
                    dict(group_name = group.name),
                forms=forms)


# END =========================================================================

/* Static JavaScript code for the Delphi 'Vote' page */

var sorting = false;
var comp_tb = {};
var comp_stack = new Array();
var qs_stack = new Array();
var n = 0;

Pair = function(first, second) {
    this.first = first;
    this.second = second;
    this.toString = function() {
        return '<' + first + ', ' + second + '>';
    }
}

cc = function(o1, o2) {
    return ranks[o1] - ranks[o2];
};

fill_vote_items = function() {
    var ul = $('#vote_items');
    ul.empty();

    for ( var j = 0; j < sorted_items.length; ++j ) {
        var i = sorted_items[j];
        li = $("<li id='li_" + i + "'></li>").html(items[i] + " <span class='delphi_ic'></span>");
        if (ranks[i] == 9999)
            li.addClass('delphi_li_i'); // ignore
        else if (ranks[i] == 9998)
            li.addClass('delphi_li_n'); // new
        else
            li.addClass('delphi_li_v'); // vote
        ul.append(li);
    }

    $('.delphi_ic').text(S3.i18n.delphi_ignore);
    $('.delphi_li_i .delphi_ic').text(S3.i18n.delphi_consider);

    $('.delphi_ic').click(function() {
        var slf = $(this);
        var item_id = slf.parent().attr('id').substr(3);
        if (ranks[item_id] == 9999) {
            ranks[item_id] = 9998;
            slf.text(S3.i18n.delphi_ignore);
            slf.parent().removeClass('delphi_li_i');
            slf.parent().addClass('delphi_li_n');
        } else {
            ranks[item_id] = 9999;
            slf.text(S3.i18n.delphi_consider);
            slf.parent().removeClass('delphi_li_n');
            slf.parent().removeClass('delphi_li_v');
            slf.parent().addClass('delphi_li_i');			
        }
    });
};

update_status = function() {
    $('#saving').hide();
    $('#saving').addClass('saved');
    $('#saving').html(S3.i18n.delphi_saved);
    $('#saving').show();

    setTimeout(function(){
        $('#saving').hide('slow');
        $('#vote_button').html(S3.i18n.delphi_update_list).show();
    }, 3000);
};

error = function(a) {
    $('#saving').html(S3.i18n.delphi_failed);
    $('#vote_button').show();
};

swap = function(ind1, ind2) {
    var tmp = sorted_items[ind1];
    sorted_items[ind1] = sorted_items[ind2];
    sorted_items[ind2] = tmp;
}

quicksort = function(left, right) {
    var pivotIndex = Math.round((left+right) / 2);
    swap(pivotIndex, right); // Move pivot to end
    for (var i = right-1; i >= left; i--)
        comp_stack.push(new Pair(i, right));
    add_comp(comp_stack.pop());
}

quicksort_init = function() {
    sorting = true;
    comp_stack = new Array();
    qs_stack = new Array();
    comp_tb = {};
    for (i in sorted_items) {
        comp_tb[sorted_items[i]] = {};
    }
    sorted_items.sort(cc);
    for(n=0; (n < sorted_items.length) && (ranks[sorted_items[n]] < 9999); n++);
    qs_stack.push(new Pair(0, n-1));
    quicksort(0, n-1);
}

add_comp = function(pair) {
    $('#comp_tr').html("<td id='cinp1' onclick='return prefer(" + pair.first + ', ' + pair.second + ");' >" + items[sorted_items[pair.first]] + "</td><td id='cinp2' onclick='return prefer(" + pair.second + ', ' + pair.first + ");' >" + items[sorted_items[pair.second]] + '</td>').show('fast').show();
}

prefer = function(first, second) {
    $('#comp_tr').hide('fast', function() {
        return prefer1(first, second);
    });
    return false;
}

prefer1 = function(first, second) {
    comp_tb[sorted_items[first]][sorted_items[second]] = -1;
    comp_tb[sorted_items[second]][sorted_items[first]] = 1;

    if (comp_stack.length > 0) {
        add_comp(comp_stack.pop());
    } else {
        var pair = qs_stack.pop();
        var left = pair.first;
        var right = pair.second;
        var pivotNewIndex = left;
        for (var i = left; i < right; i++) {
            if (comp_tb[sorted_items[right]][sorted_items[i]] == 1) {
                swap(i, pivotNewIndex);
                pivotNewIndex += 1;
            }
        }
        swap(pivotNewIndex, right); // Move pivot to its final place
        if ((pivotNewIndex - 1) > left)
            qs_stack.push(new Pair(left, pivotNewIndex - 1));
        if ((pivotNewIndex + 1) < right)
            qs_stack.push(new Pair(pivotNewIndex + 1, right));

        if ((comp_stack.length == 0) && (qs_stack.length > 0)) {
            var pair = qs_stack[qs_stack.length - 1];
            quicksort(pair.first, pair.second);
        }
        if ((comp_stack.length == 0) && (qs_stack.length == 0)) { // Sort finished
            for (i in sorted_items) {
                if (ranks[sorted_items[i]] != 9999)
                    ranks[sorted_items[i]] = '1' + i;
            }

            fill_vote_items();
            $('#vote_items').show('fast');
            var url = S3.Ap.concat('/delphi/save_vote/', problem_id);
            $.ajax({url: url,
                type: 'post',
                dataType: 'json',
                data: ranks,
                success: update_status,
                error: error
            });
            $('#saving').removeClass('saved');
            $('#saving').html(S3.i18n.delphi_saving);
            $('#saving').show('fast');
            sorting = false;
        }
    }
    return false;
}
var MFC = MFC || {};

MFC.basket = [];
MFC.origBasket = undefined;

// compare arrays
MFC.isSameSet = function( arr1, arr2 ) {
      return  $( arr1 ).not( arr2 ).length === 0 && $( arr2 ).not( arr1 ).length === 0;  
}

MFC.addRevision = function(sha) {
    $.post( "/mfcbasket/add", { 'sha': sha }, function (data) {
        MFC.updateBasket(data);
    });
}

MFC.delRevision = function(sha) {
    $.post( "/mfcbasket/remove", { 'sha': sha }, function (data) {
        MFC.updateBasket(data);
    });
}

MFC.setupCommitActionButtons = function() {
    $("#commits tr").each(function(index, element) {
        var action = $(element).find("#action")[0];
        var icon = $(action).find(".glyphicon")[0];
        var sha = $(element).attr('sha');
        var inbasket = false;
        if (MFC.basket.includes(sha)) {
            inbasket = true;
            $(icon).addClass('inbasket');
            $(action).off("click").click(function(e) {
                MFC.delRevision(sha);
            });
        }
        else {
            $(icon).removeClass('inbasket');
            $(action).off("click").click(function(e) {
                MFC.addRevision(sha);
            });
        }

        // Just to make sure we can delete MFC-ed commits from basket
        if ($(element).hasClass('mfcdone') && !inbasket) {
            $(action).addClass('hide');
        }
        else {
            $(action).removeClass('hide');
        }
    })
};

MFC.updateBasket = function(data) {
    MFC.basket = data['basket'].map(function(v) { return v.toString(); });
    if (MFC.origBasket) {
        if (MFC.isSameSet(MFC.origBasket, MFC.basket)) {
            $("#refreshbasket").addClass('disabled');
        }
        else {
            $("#refreshbasket").removeClass('disabled');
        }
    }
    else {
        MFC.origBasket = MFC.basket;
    }
    $("#mfccount").html(MFC.basket.length);
    MFC.setupCommitActionButtons();
}

MFC.fetchBasket = function() {
    $.get( "/mfcbasket/json", function( data ) {
        MFC.updateBasket(data);
    });
};

MFC.setupCommitCommentButtons = function() {
    ("#commits tr").each(function(index, element) {
        var action = $(element).find("#comment")[0];
        var sha = $(element).attr('sha');
        $(action).off("click").click(function(e) {
            MFC.addRevision(sha);
        });
    })
};

MFC.updateComment = function(sha, text, success) {
    $.post( "/commit/" + sha + "/comment", { 'text': text }, function (data) {
        success(data);
    });
}

MFC.deleteComment = function(sha, success) {
    $.ajax({
        url: "/commit/" + sha + "/comment",
        type: 'DELETE',
        success: success
    });
}

MFC.fixDependencies = function(sha, success) {
    $.ajax({
        url: "/commit/" + sha + "/fixdeps",
        type: 'POST',
        success: success
    });
}

MFC.generateShareToken = function(branch_id, success) {
    $.ajax({
        url: "/" + branch_id + "/newtoken",
        type: 'POST',
        success: success
    });
}

MFC.banCommit = function(sha, success) {
    $.ajax({
        url: "/commit/" + sha + "/ban",
        type: 'POST',
        success: success
    });
}

MFC.unbanCommit = function(sha, success) {
    $.ajax({
        url: "/commit/" + sha + "/unban",
        type: 'POST',
        success: success
    });
}

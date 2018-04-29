var MFC = MFC || {};

MFC.basket = [];
MFC.origBasket = undefined;

// compare arrays
MFC.isSameSet = function( arr1, arr2 ) {
      return  $( arr1 ).not( arr2 ).length === 0 && $( arr2 ).not( arr1 ).length === 0;  
}

MFC.addRevision = function(revision) {
    $.post( "/mfcbasket/add", { 'revision': revision }, function (data) {
        MFC.updateBasket(data);
    });
}

MFC.delRevision = function(revision) {
    $.post( "/mfcbasket/remove", { 'revision': revision }, function (data) {
        MFC.updateBasket(data);
    });
}

MFC.setupCommitActionButtons = function() {
    $("#commits tr").each(function(index, element) {
        var action = $(element).find("#action")[0];
        var icon = $(action).find(".glyphicon")[0];
        var revision = $(element).attr('revision');
        var inbasket = false;
        if (MFC.basket.includes(revision)) {
            inbasket = true;
            $(icon).addClass('inbasket');
            $(action).off("click").click(function(e) {
                MFC.delRevision(revision);
            });
        }
        else {
            $(icon).removeClass('inbasket');
            $(action).off("click").click(function(e) {
                MFC.addRevision(revision);
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
        var revision = $(element).attr('revision');
        $(action).off("click").click(function(e) {
            MFC.addRevision(revision);
        });
    })
};

MFC.updateComment = function(revision, text, success) {
    $.post( "/commit/" + revision + "/comment", { 'text': text }, function (data) {
        success(data);
    });
}

MFC.deleteComment = function(revision, success) {
    $.ajax({
        url: "/commit/" + revision + "/comment",
        type: 'DELETE',
        success: success
    });
}

MFC.fixDependencies = function(revision, success) {
    $.ajax({
        url: "/commit/" + revision + "/fixdeps",
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

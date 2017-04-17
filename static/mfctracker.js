var MFC = MFC || {};

MFC.basket = [];

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
		if (MFC.basket.includes(revision)) {
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

        if ($(element).hasClass('mfcdone')) {
            $(action).addClass('hide');
        }
        else {
            $(action).removeClass('hide');
        }
    })
};

MFC.updateBasket = function(data) {
	MFC.basket = data['basket'].map(function(v) { return v.toString(); });
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

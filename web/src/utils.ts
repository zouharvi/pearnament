import $ from 'jquery';

export function notify(message: string): void {
    /**
     * Displays a temporary notification message at the top center of the webpage.
     * The notification disappears after 4 seconds.
     * @param message - The message to be displayed in the notification.
     **/
    const notification = $('<div></div>')
        .html(message)
        .css({
            position: 'fixed',
            top: '10px',
            left: '50%',
            transform: 'translateX(-50%)',
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            color: 'white',
            padding: '10px 20px',
            borderRadius: '5px',
            zIndex: '1000'
        })
        .appendTo('body');

    setTimeout(() => {
        notification.remove();
    }, 4000);
}

// Shared types for error span annotation
export type ErrorSpan = { start_i: number, end_i: number, category: string | null, severity: string | null }
export type Response = { score: number | null, error_spans: Array<ErrorSpan> }
export type CharData = { el: JQuery<HTMLElement>, toolbox: JQuery<HTMLElement> | null, error_span: ErrorSpan | null }

// MQM Error Categories shared between pointwise and listwise
export const MQM_ERROR_CATEGORIES: { [key: string]: string[] } = {
    "Terminology": [
        "",
        "Inconsistent with terminology resource",
        "Inconsistent use of terminology",
        "Wrong term",
    ],
    "Accuracy": [
        "",
        "Mistranslation",
        "Overtranslation",
        "Undertranslation",
        "Addition",
        "Omission",
        "Do not translate",
        "Untranslated",
    ],
    "Linguistic conventions": [
        "",
        "Grammar",
        "Punctuation",
        "Spelling",
        "Unintelligible",
        "Character encoding",
        "Textual conventions",
    ],
    "Style": [
        "",
        "Organization style",
        "Third-party style",
        "Inconsistent with external reference",
        "Language register",
        "Awkward style",
        "Unidiomatic style",
        "Inconsistent style",
    ],
    "Locale convention": [
        "",
        "Number format",
        "Currency format",
        "Measurement format",
        "Time format",
        "Date format",
        "Address format",
        "Telephone format",
        "Shortcut key",
    ],
    "Audience appropriateness": [
        "",
        "Culture-specific reference",
        "Offensive",
    ],
    "Design and markup": [
        "",
        "Layout",
        "Markup tag",
        "Truncation/text expansion",
        "Missing text",
        "Link/cross-reference",
    ],
    "Other": [],
}

/**
 * Renders the progress bar for annotation tasks
 */
export function redrawProgress(current_i: number | null, progress: Array<boolean>, onItemClick?: (i: number) => void): void {
    let html = progress.map((v, i) => {
        if (i === current_i) {
            // Current item always gets the "current" highlight (larger indicator)
            return `<span class="progress_current" data-index="${i}">${i + 1}</span>`
        } else if (v) {
            return `<span class="progress_complete" data-index="${i}">${i + 1}</span>`
        } else {
            return `<span class="progress_incomplete" data-index="${i}">${i + 1}</span>`
        }
    }).join("")
    $("#progress").html(html)

    // Attach click handlers if callback is provided
    if (onItemClick) {
        $("#progress span").on("click", function() {
            const index = parseInt($(this).data("index"))
            onItemClick(index)
        })
    }
}

/**
 * Creates the span toolbox for error annotation
 */
export function createSpanToolbox(
    protocol_error_categories: boolean,
    error_span: ErrorSpan,
    tgt_chars_objs: Array<CharData>,
    left_i: number,
    right_i: number,
    onDelete: () => void
): JQuery<HTMLElement> {
    let toolbox = $(`
    <div class='span_toolbox_parent'>
    <div class='span_toolbox'>
      <div class="span_toolbox_esa" style="display: inline-block; width: 70px; padding-right: 5px;">
        <input type="button" class="error_delete" style="border-radius: 8px;" value="Remove">
        <input type="button" class="error_neutral" style="margin-top: 3px;" value="Neutral">
        <input type="button" class="error_minor" style="margin-top: 3px;" value="Minor">
        <input type="button" class="error_major" style="margin-top: 3px;" value="Major">
      </div>
      <div class="span_toolbox_mqm" style="display: inline-block; width: 140px; vertical-align: top;">
        <select style="height: 2em; width: 100%;"></select><br>
        <select style="height: 2em; width: 100%; margin-top: 3px;" disabled></select>
      </div>
    </div>
    </div>
    `)
    
    for (let category1 of Object.keys(MQM_ERROR_CATEGORIES)) {
        toolbox.find("select").eq(0).append(`<option value="${category1}">${category1}</option>`)
    }
    
    // select one category handler
    toolbox.find("select").eq(0).on("change", function () {
        let cat1 = (<HTMLSelectElement>this).value
        error_span.category = cat1
        let subcat_select = toolbox.find("select").eq(1)
        subcat_select.empty()
        let subcats = MQM_ERROR_CATEGORIES[cat1]
        subcat_select.prop("disabled", false)
        for (let subcat of subcats) {
            subcat_select.append(`<option value="${subcat}">${subcat}</option>`)
        }
        if (cat1 == "Other") {
            subcat_select.prop("disabled", true)
            error_span.category = "Other/Other"
        } else {
            error_span.category = `${cat1}`
        }
    })
    
    toolbox.find("select").eq(1).on("change", function () {
        let cat1 = toolbox.find("select").eq(0).val() as string
        let cat2 = (<HTMLSelectElement>this).value
        // enforce both category and subcategory
        if (cat2 == "" && cat1 != "Other") {
            error_span.category = `${cat1}`
        } else {
            error_span.category = `${cat1}/${cat2}`
        }
    })
    
    if (!protocol_error_categories) {
        // only MQM has neutral severity
        toolbox.find(".error_neutral").remove()
        toolbox.find(".span_toolbox_mqm").remove()
        toolbox.find(".span_toolbox_esa").css("border-right", "")
        toolbox.find(".span_toolbox_esa").css("margin-right", "-5px")
    }
    
    // handle delete button
    toolbox.find(".error_delete").on("click", () => {
        toolbox.remove()
        for (let j = left_i; j <= right_i; j++) {
            $(tgt_chars_objs[j].el).removeClass("error_unknown")
            $(tgt_chars_objs[j].el).removeClass("error_neutral")
            $(tgt_chars_objs[j].el).removeClass("error_minor")
            $(tgt_chars_objs[j].el).removeClass("error_major")
            tgt_chars_objs[j].toolbox = null
            tgt_chars_objs[j].error_span = null
        }
        onDelete()
    })
    
    // handle severity buttons
    toolbox.find(".error_neutral").on("click", () => {
        for (let j = left_i; j <= right_i; j++) {
            $(tgt_chars_objs[j].el).removeClass("error_unknown")
            $(tgt_chars_objs[j].el).removeClass("error_minor")
            $(tgt_chars_objs[j].el).removeClass("error_major")
            $(tgt_chars_objs[j].el).addClass("error_neutral")
        }
        error_span.severity = "neutral"
    })
    
    toolbox.find(".error_minor").on("click", () => {
        for (let j = left_i; j <= right_i; j++) {
            $(tgt_chars_objs[j].el).removeClass("error_unknown")
            $(tgt_chars_objs[j].el).removeClass("error_neutral")
            $(tgt_chars_objs[j].el).removeClass("error_major")
            $(tgt_chars_objs[j].el).addClass("error_minor")
        }
        error_span.severity = "minor"
    })
    
    toolbox.find(".error_major").on("click", () => {
        for (let j = left_i; j <= right_i; j++) {
            $(tgt_chars_objs[j].el).removeClass("error_unknown")
            $(tgt_chars_objs[j].el).removeClass("error_neutral")
            $(tgt_chars_objs[j].el).removeClass("error_minor")
            $(tgt_chars_objs[j].el).addClass("error_major")
        }
        error_span.severity = "major"
    })
    
    return toolbox
}

/**
 * Updates toolbox position based on character element position
 */
export function updateToolboxPosition(toolbox: JQuery<HTMLElement>, charEl: JQuery<HTMLElement>): void {
    const position = charEl.position();
    if (!position) return;
    
    const toolboxHeight = toolbox.innerHeight() || 0;
    const toolboxWidth = toolbox.innerWidth() || 0;
    const windowWidth = $(window).width() || 900;
    
    let topPosition = position.top - toolboxHeight;
    let leftPosition = position.left;
    // make sure it's not getting out of screen
    leftPosition = Math.min(leftPosition, Math.max(windowWidth, 900) - toolboxWidth + 10);

    toolbox.css({
        top: topPosition,
        left: leftPosition - 25,
    });
}
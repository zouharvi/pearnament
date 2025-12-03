import $ from 'jquery';

import { get_next_item, log_response } from './connector';
import { 
    notify, 
    ErrorSpan, 
    Response, 
    CharData, 
    MQM_ERROR_CATEGORIES, 
    redrawProgress, 
    createSpanToolbox, 
    updateToolboxPosition 
} from './utils';

// Each candidate has its own response
type CandidateResponse = { score: number | null, error_spans: Array<ErrorSpan> }
// Response for a document with multiple candidates
type DocumentResponse = Array<CandidateResponse>

type DataPayload = {
    status: string,
    progress: Array<boolean>,
    time: number,
    payload: Array<{
        src: string,
        tgt: string | Array<string>,  // Single or multiple translation candidates
        checks?: any,
        instructions?: string,
        error_spans?: Array<ErrorSpan> | Array<Array<ErrorSpan>>,  // Pre-filled error spans
    }>,
    info: {
        protocol_score: boolean,
        protocol_error_spans: boolean,
        protocol_error_categories: boolean,
        item_i: number,
    }
}
type DataFinished = {
    status: string,
    progress: Array<boolean>,
    time: number,
    token: string,
}

/**
 * Ensures tgt is always an array of candidates
 */
function ensureCandidateArray(tgt: string | Array<string>): Array<string> {
    return Array.isArray(tgt) ? tgt : [tgt]
}

/**
 * Gets error spans for a specific candidate index
 */
function getErrorSpansForCandidate(error_spans: Array<ErrorSpan> | Array<Array<ErrorSpan>> | undefined, cand_i: number, numCandidates: number): Array<ErrorSpan> {
    if (!error_spans || error_spans.length === 0) return []
    // Check if 2D array (per-candidate)
    if (error_spans.every(item => Array.isArray(item))) {
        return (error_spans as Array<Array<ErrorSpan>>)[cand_i] || []
    }
    // 1D array - only use for single candidate
    return numCandidates === 1 ? error_spans as Array<ErrorSpan> : []
}

let response_log: Array<DocumentResponse> = []
let action_log: Array<any> = []
let settings_show_alignment = true
let has_unsaved_work = false

// Prevent accidental refresh/navigation when there is ongoing work
window.addEventListener('beforeunload', (event) => {
    if (has_unsaved_work) {
        event.preventDefault()
        event.returnValue = ''
    }
})

$("#toggle_differences").on("change", function () {
    if ($(this).is(":checked")) {
        $(".difference").removeClass("hidden")
    } else {
        $(".difference").addClass("hidden")
    }
})

function check_unlock() {
    // check if all toolboxes are hidden
    for (let el of $(".span_toolbox_parent")) {
        if ($(el).css("display") != "none") {
            $("#button_next").attr("disabled", "disabled")
            $("#button_next").val("Next 🚧")
            return
        }
    }

    // check if all items are done (all candidates have scores)
    let all_done = response_log.every(doc_responses => 
        doc_responses.every(r => r.score != null)
    )
    if (!all_done) {
        $("#button_next").attr("disabled", "disabled")
        $("#button_next").val("Next 🚧")
        return
    }

    $("#button_next").removeAttr("disabled")
    $("#button_next").val("Next ✅")
}

function _slider_html(item_i: number, candidate_i: number): string {
    return `
    <div class="output_response">
      <input type="range" min="0" max="100" value="-1" id="response_${item_i}_${candidate_i}">
      <span class="slider_label">? / 100</span>
    </div>
    `
}

async function display_next_payload(response: DataPayload) {
    redrawProgress(response.info.item_i, response.progress)
    $("#time").text(`Time: ${Math.round(response.time / 60)}m`)

    let data = response.payload
    // Initialize response log for each document with responses for each candidate
    response_log = data.map(item => 
        ensureCandidateArray(item.tgt).map(_ => ({
            "score": null,
            "error_spans": [],
        }))
    )
    action_log = [{ "time": Date.now() / 1000, "action": "load" }]
    has_unsaved_work = false

    let protocol_score = response.info.protocol_score
    let protocol_error_spans = response.info.protocol_error_spans
    let protocol_error_categories = response.info.protocol_error_categories

    if (!protocol_score) $("#instructions_score").hide()
    if (!protocol_error_spans) $("#instructions_spans").hide()
    if (!protocol_error_categories) $("#instructions_categories").hide()

    $("#output_div").html("")

    for (let item_i = 0; item_i < data.length; item_i++) {
        let item = data[item_i]
        // Ensure tgt is an array of candidates
        let candidates = ensureCandidateArray(item.tgt)
        
        // character-level stuff won't work on media tags
        let no_src_char = (item.src.startsWith("<audio ") || item.src.startsWith("<video ") || item.src.startsWith("<img ") || item.src.startsWith("<iframe "))

        let src_chars = no_src_char ? item.src : item.src.split("").map(c => c == "\n" ? "<br>" : `<span class="src_char">${c}</span>`).join("")
        
        let output_block = $(`
        <div class="output_block">
          <span id="instructions_message"></span>
          <div class="output_srctgt">
            <div class="output_src">${src_chars}</div>
          </div>
        </div>
        `)

        if (item.instructions) {
            output_block.find("#instructions_message").html(item.instructions)
        }

        // Add each candidate
        let src_chars_els = no_src_char ? [] : output_block.find(".src_char").toArray()
        
        for (let cand_i = 0; cand_i < candidates.length; cand_i++) {
            let tgt = candidates[cand_i]
            let no_tgt_char = (tgt.startsWith("<audio ") || tgt.startsWith("<video ") || tgt.startsWith("<img ") || tgt.startsWith("<iframe "))
            let tgt_chars = no_tgt_char ? tgt : tgt.split("").map(c => c == "\n" ? "<br>" : `<span class="tgt_char">${c}</span>`).join("")
            
            let candidate_block = $(`
            <div class="output_candidate" data-candidate="${cand_i}">
              <div class="output_tgt">${tgt_chars}</div>
              ${protocol_score ? _slider_html(item_i, cand_i) : ""}
            </div>
            `)
            
            output_block.find(".output_srctgt").append(candidate_block)
            
            // Setup character-level interactions for this candidate
            let tgt_chars_objs: Array<CharData> = no_tgt_char ? [] : candidate_block.find(".tgt_char").toArray().map(el => ({
                "el": $(el),
                "toolbox": null,
                "error_span": null,
            }))
            let state_i: null | number = null

            if (!no_tgt_char) {
                tgt_chars_objs.forEach((obj, i) => {
                    // leaving target character
                    $(obj.el).on("mouseleave", function () {
                        $(".src_char").removeClass("highlighted")
                        $(".tgt_char").removeClass("highlighted")
                        $(".tgt_char").removeClass("highlighted_active")

                        // highlight corresponding toolbox if error severity is set
                        if (obj.error_span != null && obj.error_span.severity != null && (!protocol_error_categories || (obj.error_span.category != null && obj.error_span.category?.includes("/")))) {
                            tgt_chars_objs[i].toolbox?.css("display", "none")
                        }
                    })

                    // entering target character
                    $(obj.el).on("mouseenter", function () {
                        $(".src_char").removeClass("highlighted")
                        $(".tgt_char").removeClass("highlighted")
                        if (settings_show_alignment) {
                            // Highlight corresponding characters in source
                            let src_i = Math.round(i / tgt_chars_objs.length * src_chars_els.length)
                            for (let j = Math.max(0, src_i - 5); j <= Math.min(src_chars_els.length - 1, src_i + 5); j++) {
                                $(src_chars_els[j]).addClass("highlighted")
                            }
                            // Highlight corresponding characters in all other candidates
                            let relative_pos = i / tgt_chars_objs.length
                            output_block.find(".output_candidate").each(function() {
                                let other_tgt_chars = $(this).find(".tgt_char")
                                let other_i = Math.round(relative_pos * other_tgt_chars.length)
                                for (let j = Math.max(0, other_i - 5); j <= Math.min(other_tgt_chars.length - 1, other_i + 5); j++) {
                                    other_tgt_chars.eq(j).addClass("highlighted")
                                }
                            })
                        }
                        if (state_i != null) {
                            for (let j = Math.min(state_i, i); j <= Math.max(state_i, i); j++) {
                                $(tgt_chars_objs[j].el).addClass("highlighted")
                            }
                        }

                        // check if inside a span
                        if (tgt_chars_objs[i].error_span != null) {
                            let span = tgt_chars_objs[i].error_span!
                            // highlight the whole span if we're in one
                            for (let j = span.start_i; j <= span.end_i; j++) {
                                $(tgt_chars_objs[j].el).addClass("highlighted_active")
                            }

                            tgt_chars_objs[span.start_i].toolbox?.css("display", "block")
                        }
                    })

                    // add spans and toolbox only in case the protocol asks for it
                    if (protocol_error_spans || protocol_error_categories) {
                        $(obj.el).on("click", function () {
                            if (state_i != null) {
                                // check if we're not overlapping
                                let left_i = Math.min(state_i, i)
                                let right_i = Math.max(state_i, i)
                                state_i = null
                                $(".src_char").removeClass("highlighted")
                                candidate_block.find(".tgt_char").removeClass("highlighted")

                                let error_span: ErrorSpan = {
                                    "start_i": left_i,
                                    "end_i": right_i,
                                    "category": null,
                                    "severity": null,
                                }

                                if (response_log[item_i][cand_i].error_spans.some(span => {
                                    return (
                                        (left_i <= span.start_i && right_i >= span.start_i) ||
                                        (left_i <= span.end_i && right_i >= span.end_i)
                                    )
                                })) {
                                    notify("Cannot create overlapping error spans")
                                    return
                                }

                                // create toolbox
                                let toolbox = createSpanToolbox(
                                    protocol_error_categories,
                                    error_span,
                                    tgt_chars_objs,
                                    left_i,
                                    right_i,
                                    () => {
                                        // onDelete callback
                                        response_log[item_i][cand_i].error_spans = response_log[item_i][cand_i].error_spans.filter(span => span != error_span)
                                        action_log.push({ "time": Date.now() / 1000, "action": "delete_span", "index": item_i, "candidate": cand_i, "start_i": left_i, "end_i": right_i })
                                        has_unsaved_work = true
                                    }
                                )
                                
                                $("body").append(toolbox)
                                check_unlock()

                                // handle hover on toolbox
                                toolbox.on("mouseenter", function () {
                                    toolbox.css("display", "block")
                                    check_unlock()
                                })
                                // handle hover on toolbox
                                toolbox.on("mouseleave", function () {
                                    // hide if severity is set for ESA or both severity and category are set for MQM
                                    if (error_span.severity != null && (!protocol_error_categories || (error_span.category != null && error_span.category?.includes("/")))) {
                                        toolbox.css("display", "none")
                                        check_unlock()
                                    }
                                })

                                // set up callback to reposition toolbox on resize         
                                $(window).on('resize', function () {
                                    updateToolboxPosition(toolbox, $(tgt_chars_objs[left_i].el))
                                })
                                $(window).trigger('resize');

                                // store error span
                                response_log[item_i][cand_i].error_spans.push(error_span)
                                action_log.push({ "time": Date.now() / 1000, "action": "create_span", "index": item_i, "candidate": cand_i, "start_i": left_i, "end_i": right_i })
                                has_unsaved_work = true
                                for (let j = left_i; j <= right_i; j++) {
                                    $(tgt_chars_objs[j].el).addClass("error_unknown")
                                    tgt_chars_objs[j].toolbox = toolbox
                                    tgt_chars_objs[j].error_span = error_span
                                }
                            } else {
                                // check if we are in existing span
                                if (response_log[item_i][cand_i].error_spans.some(span => i >= span.start_i && i <= span.end_i)) {
                                    notify("Cannot create overlapping error spans")
                                    $(".src_char").removeClass("highlighted")
                                    candidate_block.find(".tgt_char").removeClass("highlighted")
                                    return
                                }

                                state_i = i
                            }
                        })
                    }
                })
            }

            // Load pre-filled error spans for this candidate
            const candidateSpans = getErrorSpansForCandidate(item.error_spans, cand_i, candidates.length)
            if (!no_tgt_char && (protocol_error_spans || protocol_error_categories) && candidateSpans.length > 0) {
                for (const prefilled of candidateSpans) {
                    const left_i = prefilled.start_i, right_i = prefilled.end_i
                    if (left_i < 0 || right_i >= tgt_chars_objs.length || left_i > right_i) continue
                    let error_span: ErrorSpan = { ...prefilled }
                    response_log[item_i][cand_i].error_spans.push(error_span)

                    let toolbox = createSpanToolbox(protocol_error_categories, error_span, tgt_chars_objs, left_i, right_i, () => {
                        response_log[item_i][cand_i].error_spans = response_log[item_i][cand_i].error_spans.filter(s => s != error_span)
                        action_log.push({ "time": Date.now() / 1000, "action": "delete_span", "index": item_i, "candidate": cand_i, "start_i": left_i, "end_i": right_i })
                        has_unsaved_work = true
                    })
                    $("body").append(toolbox)
                    toolbox.on("mouseenter", () => { toolbox.css("display", "block"); check_unlock() })
                    toolbox.on("mouseleave", () => {
                        if (error_span.severity != null && (!protocol_error_categories || (error_span.category != null && error_span.category?.includes("/")))) {
                            toolbox.css("display", "none"); check_unlock()
                        }
                    })
                    $(window).on('resize', () => updateToolboxPosition(toolbox, $(tgt_chars_objs[left_i].el)))
                    $(window).trigger('resize')
                    for (let j = left_i; j <= right_i; j++) {
                        $(tgt_chars_objs[j].el).addClass(error_span.severity ? `error_${error_span.severity}` : "error_unknown")
                        tgt_chars_objs[j].toolbox = toolbox
                        tgt_chars_objs[j].error_span = error_span
                    }
                    if (error_span.severity != null && (!protocol_error_categories || (error_span.category != null && error_span.category?.includes("/")))) {
                        toolbox.css("display", "none")
                    }
                }
            }

            // Setup slider for this candidate
            let slider = candidate_block.find("input[type='range']")
            let label = candidate_block.find(".slider_label")
            slider.on("input", function () {
                let val = parseInt((<HTMLInputElement>this).value)
                label.text(`${val}/100`)
            })
            slider.on("change", function () {
                let val = parseInt((<HTMLInputElement>this).value)
                label.text(`${val}/100`)
                response_log[item_i][cand_i].score = val
                has_unsaved_work = true
                check_unlock()
                action_log.push({ "time": Date.now() / 1000, "index": item_i, "candidate": cand_i, "value": val })
            })
        }

        // Source character hover effects
        if (!no_src_char) {
            src_chars_els.forEach((obj, i) => {
                $(obj).on("mouseleave", function () {
                    $(".src_char").removeClass("highlighted")
                    $(".tgt_char").removeClass("highlighted")
                })

                $(obj).on("mouseenter", function () {
                    $(".tgt_char").removeClass("highlighted")
                    if (settings_show_alignment) {
                        // Highlight corresponding characters in all candidates
                        output_block.find(".output_candidate").each(function() {
                            let tgt_chars = $(this).find(".tgt_char")
                            let tgt_i = Math.round(i / src_chars_els.length * tgt_chars.length)
                            for (let j = Math.max(0, tgt_i - 5); j <= Math.min(tgt_chars.length - 1, tgt_i + 5); j++) {
                                tgt_chars.eq(j).addClass("highlighted")
                            }
                        })
                    }
                })
            })
        }
        
        $("#output_div").append(output_block)
    }

    check_unlock()
}


let payload: DataPayload | null = null
async function display_next_item() {
    let response = await get_next_item<DataPayload | DataFinished>()
    has_unsaved_work = false

    if (response == null) {
        notify("Error fetching the next item. Please try again later.")
        return
    }

    if (response.status == "completed") {
        let response_finished = response as DataFinished
        $("#output_div").html(`
    <div class='white-box' style='width: max-content'>
    <h2>🎉 All done, thank you for your annotations!</h2>

    If someone asks you for a token of completion, show them
    <span style="font-family: monospace; font-size: 11pt; padding: 5px;">${response_finished.token}</span>
    <br>
    <br>
    </div>
    `)
        redrawProgress(null, response_finished.progress)
        $("#time").text(`Time: ${Math.round(response_finished.time / 60)}m`)
        // NOTE: re-enable if we want to allow going back
        $("#button_settings").hide()
        $("#button_next").hide()
    } else if (response.status == "ok") {
        payload = response as DataPayload
        display_next_payload(response as DataPayload)
    } else {
        console.error("Non-ok response", response)
    }
}

$("#button_next").on("click", async function () {
    // disable while communicating with the server
    $("#button_next").attr("disabled", "disabled")
    $("#button_next").val("Next 📶")
    action_log.push({ "time": Date.now() / 1000, "action": "submit" })
    let outcome = await log_response(
        { "annotations": response_log, "actions": action_log, "item": payload },
        payload!.info.item_i,
    )
    if (outcome == null || outcome == false) {
        notify("Error submitting the annotations. Please try again.")
        $("#button_next").removeAttr("disabled")
        $("#button_next").val("Next ❓")
        return
    }
    await display_next_item()
})

display_next_item()

// toggle settings display
$("#button_settings").on("click", function () {
    $("#settings_div").toggle()
})

// load settings from localStorage
$("#settings_approximate_alignment").on("change", function () {
    settings_show_alignment = $("#settings_approximate_alignment").is(":checked")
    localStorage.setItem("setting_approximate_alignment", settings_show_alignment.toString())
})
$("#settings_approximate_alignment").prop("checked", localStorage.getItem("setting_approximate_alignment") == "true")
$("#settings_approximate_alignment").trigger("change")

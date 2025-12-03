import $ from 'jquery';

import { get_next_item, get_i_item, log_response } from './connector';
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
type DataPayload = {
  status: string,
  progress: Array<boolean>,
  time: number,
  payload: Array<{
    src: string,
    tgt: string,
    checks?: any,
    instructions?: string,
    error_spans?: Array<ErrorSpan>,
  }>,
  payload_existing?: Array<Response>,
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
let response_log: Array<Response> = []
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

  // check if all items are done
  if (!response_log.every(r => r.score != null)) {
    $("#button_next").attr("disabled", "disabled")
    $("#button_next").val("Next 🚧")
    return
  }

  $("#button_next").removeAttr("disabled")
  $("#button_next").val("Next ✅")
}

function _slider_html(i: number): string {
  return `
      <div class="output_response">
        <input type="range" min="0" max="100" value="-1" id="response_${i}" orient="vertical">
        <br>
        <label class="output_number">?</label>
      </div>
      <div class="output_labels">
        100: perfect <br>
        66: middling <br>
        33: broken <br>
        0: nonsense
      </div>
    `
}

async function display_next_payload(response: DataPayload) {
  redrawProgress(response.info.item_i, response.progress, navigate_to_item)
  $("#time").text(`Time: ${Math.round(response.time / 60)}m`)

  let data = response.payload
  // If payload_existing exists (previously submitted annotations), use it; otherwise initialize empty
  if (response.payload_existing) {
    response_log = response.payload_existing.map(r => ({
      "score": r.score,
      "error_spans": r.error_spans ? [...r.error_spans] : [],
    }))
  } else {
    response_log = data.map(_ => ({
      "score": null,
      "error_spans": [],
    }))
  }
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
    // character-level stuff won't work on media tags
    let no_src_char = (item.src.startsWith("<audio ") || item.src.startsWith("<video ") || item.src.startsWith("<img ") || item.src.startsWith("<iframe "))
    let no_tgt_char = (item.tgt.startsWith("<audio ") || item.tgt.startsWith("<video ") || item.tgt.startsWith("<img ") || item.tgt.startsWith("<iframe "))

    let src_chars = no_src_char ? item.src : item.src.split("").map(c => c == "\n" ? "<br>" : `<span class="src_char">${c}</span>`).join("")
    let tgt_chars = no_tgt_char ? item.tgt : item.tgt.split("").map(c => c == "\n" ? "<br>" : `<span class="tgt_char">${c}</span>`).join("")
    let output_block = $(`
      <div class="output_block">
      <span id="instructions_message"></span>
      <div class="output_srctgt">
        <div class="output_src">${src_chars}</div>
        <div class="output_tgt">${tgt_chars}</div>
      </div>
      ${protocol_score ? _slider_html(item_i) : ""}
      </div>
    `)

    if (item.instructions) {
      output_block.find("#instructions_message").html(item.instructions)
    }

    // crude character alignment
    let src_chars_els = no_src_char ? [] : output_block.find(".src_char").toArray()
    let tgt_chars_objs: Array<CharData> = no_tgt_char ? [] : output_block.find(".tgt_char").toArray().map(el => ({
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
          if (settings_show_alignment) {
            let src_i = Math.round(i / tgt_chars_objs.length * src_chars_els.length)
            for (let j = Math.max(0, src_i - 5); j <= Math.min(src_chars_els.length - 1, src_i + 5); j++) {
              $(src_chars_els[j]).addClass("highlighted")
            }
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
              $(".tgt_char").removeClass("highlighted")

              let error_span: ErrorSpan = {
                "start_i": left_i,
                "end_i": right_i,
                "category": null,
                "severity": null,
              }

              if (response_log[item_i].error_spans.some(span => {
                return (
                  (left_i <= span.start_i && right_i >= span.start_i) ||
                  (left_i <= span.end_i && right_i >= span.end_i)
                )
              })) {
                notify("Cannot create overlapping error spans")
                return
              }

              // create a new toolbox at the top of the first character
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
                // @ts-ignore
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
                // enfore both category and subcategory
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
              // handle delete button
              toolbox.find(".error_delete").on("click", () => {
                // remove toolbox
                toolbox.remove()
                for (let j = left_i; j <= right_i; j++) {
                  // remove highlighting
                  $(tgt_chars_objs[j].el).removeClass("error_unknown")
                  $(tgt_chars_objs[j].el).removeClass("error_neutral")
                  $(tgt_chars_objs[j].el).removeClass("error_minor")
                  $(tgt_chars_objs[j].el).removeClass("error_major")
                  tgt_chars_objs[j].toolbox = null
                  tgt_chars_objs[j].error_span = null
                }
                // remove from response log
                response_log[item_i].error_spans = response_log[item_i].error_spans.filter(span => span != error_span)
                action_log.push({ "time": Date.now() / 1000, "action": "delete_span", "index": item_i, "start_i": left_i, "end_i": right_i })
                has_unsaved_work = true
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

              // set up callback to reposition toolbox on resize         
              $(window).on('resize', function () {
                let topPosition = $(tgt_chars_objs[left_i].el).position()?.top - toolbox.innerHeight()!;
                let leftPosition = $(tgt_chars_objs[left_i].el).position()?.left;
                // make sure it's not getting out of screen
                leftPosition = Math.min(leftPosition, Math.max($(window).width()!, 900) - toolbox.innerWidth()! + 10);

                toolbox.css({
                  top: topPosition,
                  left: leftPosition - 25,
                });
              })
              $(window).trigger('resize');

              // store error span
              response_log[item_i].error_spans.push(error_span)
              action_log.push({ "time": Date.now() / 1000, "action": "create_span", "index": item_i, "start_i": left_i, "end_i": right_i })
              has_unsaved_work = true
              for (let j = left_i; j <= right_i; j++) {
                $(tgt_chars_objs[j].el).addClass("error_unknown")
                tgt_chars_objs[j].toolbox = toolbox
                tgt_chars_objs[j].error_span = error_span
              }
            } else {
              // check if we are in existing span
              if (response_log[item_i].error_spans.some(span => i >= span.start_i && i <= span.end_i)) {
                notify("Cannot create overlapping error spans")
                $(".src_char").removeClass("highlighted")
                $(".tgt_char").removeClass("highlighted")
                return
              }

              state_i = i
            }
          })
        }
      })
    }

    // Load error spans - use payload_existing if available, otherwise use item.error_spans
    const existingErrorSpans = response.payload_existing?.[item_i]?.error_spans
    const errorSpansToLoad = existingErrorSpans || item.error_spans || []
    
    if (!no_tgt_char && (protocol_error_spans || protocol_error_categories) && errorSpansToLoad.length > 0) {
      // Only reset if loading from payload_existing (to avoid duplicating pre-filled spans)
      if (existingErrorSpans) {
        response_log[item_i].error_spans = []
      }
      
      for (const prefilled of errorSpansToLoad) {
        const left_i = prefilled.start_i, right_i = prefilled.end_i
        if (left_i < 0 || right_i >= tgt_chars_objs.length || left_i > right_i) continue
        let error_span: ErrorSpan = { ...prefilled }
        response_log[item_i].error_spans.push(error_span)

        let toolbox = createSpanToolbox(protocol_error_categories, error_span, tgt_chars_objs, left_i, right_i, () => {
          response_log[item_i].error_spans = response_log[item_i].error_spans.filter(s => s != error_span)
          action_log.push({ "time": Date.now() / 1000, "action": "delete_span", "index": item_i, "start_i": left_i, "end_i": right_i })
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

    if (!no_src_char) {
      src_chars_els.forEach((obj, i) => {
        $(obj).on("mouseleave", function () {
          $(".src_char").removeClass("highlighted")
          $(".tgt_char").removeClass("highlighted")
        })

        $(obj).on("mouseenter", function () {
          $(".tgt_char").removeClass("highlighted")
          if (settings_show_alignment) {
            let tgt_i = Math.round(i / src_chars_els.length * tgt_chars_objs.length)
            for (let j = Math.max(0, tgt_i - 5); j <= Math.min(tgt_chars_objs.length - 1, tgt_i + 5); j++) {
              $(tgt_chars_objs[j].el).addClass("highlighted")
            }
          }
        })
      })
    }
    $("#output_div").append(output_block)

    let slider = output_block.find("input[type='range']")
    let label = output_block.find(".output_number")
    slider.on("input", function () {
      let val = parseInt((<HTMLInputElement>this).value)
      label.text(val.toString())
    })
    slider.on("change", function () {
      let val = parseInt((<HTMLInputElement>this).value)
      label.text(val.toString())
      let i = parseInt(slider.attr("id")!.split("_")[1])
      response_log[i].score = val
      has_unsaved_work = true
      check_unlock()
      action_log.push({ "time": Date.now() / 1000, "index": i, "value": val })
    })
    
    // Pre-fill score from payload_existing if available
    const existingScore = response.payload_existing?.[item_i]?.score
    if (existingScore != null && protocol_score) {
      slider.val(existingScore)
      label.text(existingScore.toString())
      response_log[item_i].score = existingScore
    }
  }

  check_unlock()
}


let payload: DataPayload | null = null
async function navigate_to_item(item_i: number) {
  // Fetch and display a specific item by index
  let response = await get_i_item<DataPayload | DataFinished>(item_i)
  has_unsaved_work = false

  if (response == null) {
    notify("Error fetching the item. Please try again later.")
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
    redrawProgress(null, response_finished.progress, navigate_to_item)
    $("#time").text(`Time: ${Math.round(response_finished.time / 60)}m`)
    $("#button_settings").hide()
    $("#button_next").hide()
  } else if (response.status == "ok") {
    payload = response as DataPayload
    display_next_payload(response as DataPayload)
  } else {
    console.error("Non-ok response", response)
  }
}

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
    redrawProgress(null, response_finished.progress, navigate_to_item)
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
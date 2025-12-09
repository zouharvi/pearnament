import $ from 'jquery';

import { get_next_item, get_i_item, log_response } from './connector';
import {
  notify,
  ErrorSpan,
  Response,
  CharData,
  redrawProgress,
  createSpanToolbox,
  updateToolboxPosition,
  Validation,
  validateResponse,
  hasAllowSkip,
  DataFinished,
  ProtocolInfo,
  displayCompletionScreen,
  isMediaContent,
  contentToCharSpans,
  isSpanComplete,
  computeWordBoundaries,
} from './utils';

// Check if frozen mode is enabled (view-only, no annotations)
const searchParams = new URLSearchParams(window.location.search)
const frozenMode = searchParams.has("frozen")

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
    validation?: Validation,
  }>,
  payload_existing?: {
    annotations: Array<Response>,
    comment?: string
  },
  info: ProtocolInfo
}
let response_log: Array<Response> = []
let action_log: Array<any> = []
let validations: Array<Validation | undefined> = []
let output_blocks: Array<JQuery<HTMLElement>> = []
let settings_show_alignment = true
let settings_word_level = false
let has_unsaved_work = false
let skip_tutorial_mode = false
// Protocol settings for check_unlock
let protocol_score = false
let protocol_error_spans = false
let protocol_error_categories = false

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
  // In frozen mode, always keep the button disabled
  if (frozenMode) {
    $("#button_next").attr("disabled", "disabled")
    $("#button_next").val("Next 🔒")
    return
  }

  // Check if all error spans are complete (have required severity and category based on protocol)
  if (protocol_error_spans || protocol_error_categories) {
    for (const r of response_log) {
      for (const span of r.error_spans) {
        if (!isSpanComplete(span, protocol_error_categories)) {
          $("#button_next").attr("disabled", "disabled")
          $("#button_next").val("Next 🚧")
          return
        }
      }
    }
  }

  // Check if all scores are set (if protocol requires scores)
  if (protocol_score && !response_log.every(r => r.score != null)) {
    $("#button_next").attr("disabled", "disabled")
    $("#button_next").val("Next 🚧")
    return
  }

  $("#button_next").removeAttr("disabled")
  $("#button_next").val("Next ✅")
}

/**
 * Cleanup function to remove toolboxes and handlers from previous item
 * Must be called before loading a new item to prevent memory leaks and stale UI
 */
function cleanupPreviousItem(): void {
  // Remove all toolboxes appended to body
  $(".span_toolbox_parent").remove()
  // Remove resize handlers for toolbox positioning (use namespace to avoid removing other handlers)
  $(window).off('resize.toolbox')
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
  // Cleanup toolboxes and handlers from previous item
  cleanupPreviousItem()

  redrawProgress(response.info.item_i, response.progress, navigate_to_item)
  $("#time").text(`Time: ${Math.round(response.time / 60)}m`)

  let data = response.payload
  // If payload_existing exists (previously submitted annotations), use it; otherwise initialize empty
  if (response.payload_existing) {
    response_log = response.payload_existing.annotations.map(r => ({
      "score": r.score,
      "error_spans": r.error_spans ? [...r.error_spans] : [],
    }))
    // Reload comment if it exists
    if (response.payload_existing.comment) {
      $("#settings_comment").val(response.payload_existing.comment)
    } else {
      $("#settings_comment").val("")
    }
  } else {
    response_log = data.map(_ => ({
      "score": null,
      "error_spans": [],
    }))
    $("#settings_comment").val("")
  }
  validations = data.map(item => item.validation)
  output_blocks = []
  action_log = [{ "time": Date.now() / 1000, "action": "load" }]
  has_unsaved_work = false
  skip_tutorial_mode = false

  // Show/hide skip tutorial button based on validation settings
  if (hasAllowSkip(validations)) {
    $("#button_skip_tutorial").show()
  } else {
    $("#button_skip_tutorial").hide()
  }

  protocol_score = response.info.protocol_score
  protocol_error_spans = response.info.protocol_error_spans
  protocol_error_categories = response.info.protocol_error_categories

  if (!protocol_score) $("#instructions_score").hide()
  if (!protocol_error_spans) $("#instructions_spans").hide()
  if (!protocol_error_categories) $("#instructions_categories").hide()

  $("#output_div").html("")

  for (let item_i = 0; item_i < data.length; item_i++) {
    let item = data[item_i]
    // character-level stuff won't work on media tags
    let no_src_char = isMediaContent(item.src)
    let no_tgt_char = isMediaContent(item.tgt)

    let src_chars = no_src_char ? item.src : contentToCharSpans(item.src, "src_char")
    let tgt_chars = no_tgt_char ? item.tgt : (contentToCharSpans(item.tgt, "tgt_char") + (protocol_error_spans ? ' <span class="tgt_char char_missing">[missing]</span>' : ""))
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
    let _tgt_chars_els = output_block.find(".tgt_char").toArray()
    // Compute word boundaries for the target text. Use _tgt_chars_els because we might skip/collapse some chars
    let tgt_word_boundaries = no_tgt_char ? [] : computeWordBoundaries(_tgt_chars_els.map(el => $(el).text()))
    let tgt_chars_objs: Array<CharData> = no_tgt_char ? [] : _tgt_chars_els.map((el, idx) => ({
      "el": $(el),
      "toolbox": null,
      "error_span": null,
      "word_start": idx < tgt_word_boundaries.length ? tgt_word_boundaries[idx][0] : idx,
      "word_end": idx < tgt_word_boundaries.length ? tgt_word_boundaries[idx][1] : idx,
    }))
    let state_i: null | number = null
    let missing_i = protocol_error_spans ? tgt_chars_objs.findIndex(obj => obj.el.hasClass("char_missing")) : -1

    if (!no_tgt_char) {
      tgt_chars_objs.forEach((obj, i) => {
        let is_missing = (i == missing_i)
        
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
          if (settings_show_alignment && !is_missing) {
            let src_i = Math.round(i / tgt_chars_objs.length * src_chars_els.length)
            for (let j = Math.max(0, src_i - 5); j <= Math.min(src_chars_els.length - 1, src_i + 5); j++) {
              $(src_chars_els[j]).addClass("highlighted")
            }
          }
          if (state_i != null && !is_missing) {
            // In word-level mode, expand selection preview to word boundaries
            let preview_left = Math.min(state_i, i)
            let preview_right = Math.max(state_i, i)
            if (settings_word_level && state_i != missing_i) {
              preview_left = tgt_chars_objs[preview_left].word_start
              preview_right = tgt_chars_objs[preview_right].word_end
            }
            for (let j = preview_left; j <= preview_right; j++) {
              $(tgt_chars_objs[j].el).addClass("highlighted")
            }
          } else if (settings_word_level && !is_missing && state_i == null) {
            // Highlight current word on hover when in word-level mode (no active selection)
            for (let j = obj.word_start; j <= obj.word_end; j++) {
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
            // In frozen mode, do not allow creating new error spans
            if (frozenMode) return

            if (is_missing) {
              state_i = missing_i
            }
            if (state_i != null) {
              // check if we're not overlapping
              let left_i = Math.min(state_i, i)
              let right_i = Math.max(state_i, i)
              
              // Expand to word boundaries if word-level mode is enabled
              if (settings_word_level && !is_missing && state_i != missing_i) {
                left_i = tgt_chars_objs[left_i].word_start
                right_i = tgt_chars_objs[right_i].word_end
              }
              
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

              // create toolbox using shared utility
              let toolbox = createSpanToolbox(
                protocol_error_categories,
                error_span,
                tgt_chars_objs,
                left_i,
                right_i,
                () => {
                  // onDelete callback
                  response_log[item_i].error_spans = response_log[item_i].error_spans.filter(span => span != error_span)
                  action_log.push({ "time": Date.now() / 1000, "action": "delete_span", "index": item_i, "start_i": left_i, "end_i": right_i })
                  has_unsaved_work = true
                },
                frozenMode
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
              $(window).on('resize.toolbox', () => updateToolboxPosition(toolbox, $(tgt_chars_objs[left_i].el)))
              updateToolboxPosition(toolbox, $(tgt_chars_objs[left_i].el))

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
    const existingErrorSpans = response.payload_existing?.annotations[item_i]?.error_spans
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
        }, frozenMode)
        $("body").append(toolbox)
        toolbox.on("mouseenter", () => { toolbox.css("display", "block"); check_unlock() })
        toolbox.on("mouseleave", () => {
          if (error_span.severity != null && (!protocol_error_categories || (error_span.category != null && error_span.category?.includes("/")))) {
            toolbox.css("display", "none"); check_unlock()
          }
        })
        $(window).on('resize.toolbox', () => updateToolboxPosition(toolbox, $(tgt_chars_objs[left_i].el)))

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
    output_blocks.push(output_block)

    let slider = output_block.find("input[type='range']")
    let label = output_block.find(".output_number")
    slider.on("input", function () {
      // In frozen mode, do not allow changing scores
      if (frozenMode) return

      let val = parseInt((<HTMLInputElement>this).value)
      label.text(val.toString())
      
      // val == 0 is the only case when 'change' does not fire
      if (val == 0) {
          let i = parseInt(slider.attr("id")!.split("_")[1])
          response_log[i].score = val
          has_unsaved_work = true
          check_unlock()
          action_log.push({ "time": Date.now() / 1000, "action": "score", "index": i, "value": val })
      }
    })
    slider.on("change", function () {
      // In frozen mode, do not allow changing scores
      if (frozenMode) return

      let val = parseInt((<HTMLInputElement>this).value)
      label.text(val.toString())
      let i = parseInt(slider.attr("id")!.split("_")[1])
      response_log[i].score = val
      has_unsaved_work = true
      check_unlock()
      // push only for change which happens just once
      action_log.push({ "time": Date.now() / 1000, "action": "score", "index": i, "value": val })
    })

    // Disable slider in frozen mode
    if (frozenMode) {
      slider.prop("disabled", true)
    }

    // Pre-fill score from payload_existing if available
    const existingScore = response.payload_existing?.annotations[item_i]?.score
    if (existingScore != null && protocol_score) {
      slider.val(existingScore)
      label.text(existingScore.toString())
      response_log[item_i].score = existingScore
    }
  }

  // trigger once to reposition toolboxes
  $(window).trigger('resize.toolbox')
  check_unlock()
}


let payload: DataPayload | null = null
async function navigate_to_item(item_i: number) {
  // Warn if there's unsaved work
  if (has_unsaved_work) {
    if (!confirm("You have unsaved work. Are you sure you want to navigate away?")) {
      return
    }
  }

  // Fetch and display a specific item by index
  let response = await get_i_item<DataPayload | DataFinished>(item_i)
  has_unsaved_work = false

  if (response == null) {
    notify("Error fetching the item. Please try again later.")
    return
  }

  if (response.status == "completed") {
    displayCompletionScreen(response as DataFinished, navigate_to_item)
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
    displayCompletionScreen(response as DataFinished, navigate_to_item)
  } else if (response.status == "ok") {
    payload = response as DataPayload
    display_next_payload(response as DataPayload)
  } else {
    console.error("Non-ok response", response)
  }
}

/**
 * Validate all responses and handle failures
 * Returns true if we can continue (can still happen even on failed validation if no warnings are set).
 */
async function performValidation(): Promise<Array<boolean> | null> {
  $(".validation_warning").remove()

  let results: Array<boolean> = []
  for (let item_ij = 0; item_ij < response_log.length; item_ij++) {
    if (validations[item_ij] == undefined) {
      continue
    }
    const result = validateResponse(response_log[item_ij], validations[item_ij] as Validation)

    // if we fail and there's a message, prevent loading next item and show warning
    if (!result && validations[item_ij]?.warning) {
      // Scroll to the block
      if (output_blocks[item_ij] && output_blocks[item_ij].offset()) {
        $('html, body').animate({ scrollTop: output_blocks[item_ij].offset()!.top - 100 }, 500)
      }
      // Show warning indicator
      output_blocks[item_ij].find(".validation_warning").remove()
      const warningEl = $(`<span class="validation_warning" title="${validations[item_ij]?.warning || 'Validation failed'}">⚠️</span>`)
      output_blocks[item_ij].prepend(warningEl)
      notify(validations[item_ij]?.warning as string)
      return null
    }

    results.push(result)
  }

  // TODO: log this incident

  return results
}

$("#button_next").on("click", async function () {
  let validationResult
  // Perform validation unless in skip tutorial mode
  if (!skip_tutorial_mode) {
    validationResult = await performValidation()
    if (validationResult == null) {
      // Validation failed, don't proceed
      return
    }
  }

  // disable while communicating with the server
  $("#button_next").attr("disabled", "disabled")
  $("#button_next").val("Next 📶")
  action_log.push({ "time": Date.now() / 1000, "action": "submit" + (skip_tutorial_mode ? "_skip" : "") })

  let payload_local = { "annotations": response_log, "actions": action_log, "item": payload?.payload, }
  if (!skip_tutorial_mode && validationResult!.length > 0) {
    // @ts-ignore
    payload_local["validations"] = validationResult
  }
  
  // Include comment if provided
  const comment = $("#settings_comment").val() as string
  if (comment && comment.trim() !== "") {
    // @ts-ignore
    payload_local["comment"] = comment.trim()
    // Clear comment after submission
    $("#settings_comment").val("")
  }
  
  let outcome = await log_response(payload_local, payload!.info.item_i)
  if (outcome == null || outcome == false) {
    notify("Error submitting the annotations. Please try again.")
    $("#button_next").removeAttr("disabled")
    $("#button_next").val("Next ❓")
    return
  }
  await display_next_item()
})

// Skip tutorial button handler
$("#button_skip_tutorial").on("click", function () {
  skip_tutorial_mode = true
  notify("Tutorial skipped. Your current annotations will be submitted.")
  // Trigger the next button click
  $("#button_next").trigger("click")
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

// word-level annotation setting
$("#settings_word_level").on("change", function () {
  settings_word_level = $("#settings_word_level").is(":checked")
  localStorage.setItem("setting_word_level", settings_word_level.toString())
})
$("#settings_word_level").prop("checked", localStorage.getItem("setting_word_level") == "true")
$("#settings_word_level").trigger("change")
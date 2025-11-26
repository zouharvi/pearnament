import $ from 'jquery';

import { get_next_item, log_response } from './connector';
import { notify } from './utils';
type ErrorSpan = { "start_i": number, "end_i": number, "category": string | null, "severity": string | null, }
type Response = { "done": boolean, "score": number | null, "error_spans": Array<ErrorSpan>, }
type CharData = { "el": JQuery<HTMLElement>, "toolbox": JQuery<HTMLElement> | null, "error_span": ErrorSpan | null, }
let response_log: Array<Response> = []
let action_log: Array<any> = []

const MQM_ERROR_CATEGORIES = {
  "Terminology": [
    "Inconsistent with terminology resource",
    "Inconsistent use of terminology",
    "Wrong term",
  ],
  "Accuracy": [
    "Mistranslation",
    "Overtranslation",
    "Undertranslation",
    "Addition",
    "Omission",
    "Do not translate",
    "Untranslated",
  ],
  "Linguistic conventions": [
    "Grammar",
    "Punctuation",
    "Spelling",
    "Unintelligible",
    "Character encoding",
    "Textual conventions",
  ],
  "Style": [
    "Organization style",
    "Third-party style",
    "Inconsistent with external reference",
    "Language register",
    "Awkward style",
    "Unidiomatic style",
    "Inconsistent style",
  ],
  "Locale convention": [
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
    "Culture-specific reference",
    "Offensive",
  ],
  "Design and markup": [
    "Layout",
    "Markup tag",
    "Truncation/text expansion",
    "Missing text",
    "Link/cross-reference",
  ],
  "Other": [],
}

$("#toggle_differences").on("change", function () {
  if ($(this).is(":checked")) {
    $(".difference").removeClass("hidden")
  } else {
    $(".difference").addClass("hidden")
  }
})

function check_unlock() {
  if (response_log.every(r => r.done)) {
    $("#button_next").removeAttr("disabled")
    $("#button_next").val("Next ✅")
  } else {
    $("#button_next").attr("disabled", "disabled")
    $("#button_next").val("Next 🚧")
  }
}

export type DataPayload = {
  "status": string,
  "progress": { "completed": number, "total": number, "time": number },
  "payload": { "src": Array<string>, "tgt": Array<string> },
  "info": {
    "status_message": string,
    "protocol_score": boolean,
    "protocol_error_spans": boolean,
    "protocol_error_categories": boolean,
  }
}
export type DataFinished = {
  "status": string,
  "progress": { "completed": number, "total": number, "time": number, },
  "token": string,
}

function _slider_html(i: number): string {
  return `
      <div class="output_response">
        <input type="range" min="0" max="100" value="-1" id="response_${i}" orient="vertical">
        <br>
        <label class="output_number">?</label>
      </div>
      <div class="output_labels">
        100: perfect
        <br>
        <br>
        <br>
        66: middling
        <br>
        <br>
        <br>
        33: broken
        <br>
        <br>
        <br>
        0: nonsense
      </div>
    `
}


async function display_next_payload(response: DataPayload) {
  $("#progress").text(`Progress: ${response.progress.completed}/${response.progress.total}`)
  $("#time").text(`Annotation time: ${Math.round(response.progress.time / 60)}m`)

  let data = response.payload
  response_log = data.src.map(_ => ({
    "done": false,
    "score": null,
    "error_spans": [],
  }))
  action_log = [{ "time": Date.now() / 1000, "action": "load" }]

  $("#status_message").html(response.info.status_message)

  let protocol_score = response.info.protocol_score
  let protocol_error_spans = response.info.protocol_error_spans
  let protocol_error_categories = response.info.protocol_error_categories

  $("#output_div").html("")

  for (let item_i = 0; item_i < data.src.length; item_i++) {
    let src_chars = data.src[item_i].split("").map(c => `<span class="src_char">${c}</span>`).join("")
    let tgt_chars = data.tgt[item_i].split("").map(c => `<span class="tgt_char">${c}</span>`).join("")
    let output_block = $(`
      <div class="output_block">
      <div class="output_srctgt">
        <div class="output_src">${src_chars}</div>
        <div class="output_tgt">${tgt_chars}</div>
      </div>
      ${protocol_score ? _slider_html(item_i) : ""}
      </div>
    `)

    // crude character alignment
    let src_chars_els = output_block.find(".src_char").toArray()
    let tgt_chars_objs: Array<CharData> = output_block.find(".tgt_char").toArray().map(el => ({
      "el": $(el),
      "toolbox": null,
      "error_span": null,
    }))
    let state_i: null | number = null

    tgt_chars_objs.forEach((obj, i) => {
      $(obj.el).on("mouseleave", function () {
        $(".src_char").removeClass("highlighted")
        $(".tgt_char").removeClass("highlighted")
        $(".tgt_char").removeClass("highlighted_active")

        // gracefully hide toolbox if toolbox itself is not being hovered and severity is set

        // highlight corresponding toolbox if error severity is set
        if (obj.error_span != null && obj.error_span.severity != null && (!protocol_error_categories || (obj.error_span.category != null && obj.error_span.category?.includes("/")))) {
          tgt_chars_objs[i].toolbox?.css("display", "none")
        }
      })

      $(obj.el).on("mouseenter", function () {
        $(".src_char").removeClass("highlighted")
        let src_i = Math.round(i / tgt_chars_objs.length * src_chars_els.length)
        for (let j = Math.max(0, src_i - 5); j <= Math.min(src_chars_els.length - 1, src_i + 5); j++) {
          $(src_chars_els[j]).addClass("highlighted")
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

          // TODO: change location of toolbox to follow span even after screen change
          // TODO: make sure it's not getting out of screen
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
              <div class="span_toolbox_esa" style="display: inline-block; width: 70px; padding-right: 5px; border-right: 2px solid white;">
                <input type="button" class="error_delete" style="border-radius: 5px;" value="Remove">
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
              error_span.category = `${cat1}`
            })
            toolbox.find("select").eq(1).on("change", function () {
              let cat1 = toolbox.find("select").eq(0).val() as string
              let cat2 = (<HTMLSelectElement>this).value
              error_span.category = `${cat1}/${cat2}`
            })

            if (!protocol_error_categories) {
              // only MQM has neutral severity
              toolbox.find(".error_neutral").remove()
              toolbox.find(".span_toolbox_mqm").remove()
              toolbox.find(".span_toolbox_esa").css("border-right", "")
              toolbox.find(".span_toolbox_esa").css("margin-right", "-5px")
            }
            $("body").append(toolbox)

            // handle hover
            toolbox.on("mouseenter", function () {
              toolbox.css("display", "block")
            })
            toolbox.on("mouseleave", function () {
              // hide if severity is set
              if (error_span.severity != null && (!protocol_error_categories || (error_span.category != null && error_span.category?.includes("/")))) {
                toolbox.css("display", "none")
              }
            })
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

            const topPosition = $(tgt_chars_objs[left_i].el).position()?.top - toolbox.outerHeight()!;
            const leftPosition = $(tgt_chars_objs[left_i].el).position()?.left;

            toolbox.css({
              top: topPosition,
              left: leftPosition - 25,
            });


            response_log[item_i].error_spans.push(error_span)
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

    src_chars_els.forEach((obj, i) => {
      $(obj).on("mouseleave", function () {
        $(".src_char").removeClass("highlighted")
        $(".tgt_char").removeClass("highlighted")
      })

      $(obj).on("mouseenter", function () {
        $(".tgt_char").removeClass("highlighted")
        let tgt_i = Math.round(i / src_chars_els.length * tgt_chars_objs.length)
        for (let j = Math.max(0, tgt_i - 5); j <= Math.min(tgt_chars_objs.length - 1, tgt_i + 5); j++) {
          $(tgt_chars_objs[j].el).addClass("highlighted")
        }
      })
    })
    $("#output_div").append(output_block)

    let slider = output_block.find("input[type='range']")
    let label = output_block.find(".output_number")
    slider.on("input", function () {
      let val = parseInt((<HTMLInputElement>this).value)
      label.text(val.toString())
      let i = parseInt(slider.attr("id")!.split("_")[1])
      response_log[i].score = val
      response_log[i].done = true
      check_unlock()
      action_log.push({ "time": Date.now() / 1000, "index": i, "value": val })
    })
  }

  check_unlock()
}


async function load_next() {
  let response = await get_next_item<DataPayload | DataFinished>()

  if (response.status == "completed") {
    let response_finished = response as DataFinished
    $("#output_div").html(`
    <div class='white-box' style='width: max-content'>
    <h2>🎉 All done, thank you for your annotations!</h2>

    If someone asks you for a token of completion, show them:
    <span style="font-family: monospace; font-size: 11pt;">${response_finished.token}</span>
    <br>
    <br>
    </div>
    `)
    $("#progress").text(`Progress: ${response.progress.completed}/${response.progress.total}`)
    $("#time").text(`Total annotation time: ${Math.round(response_finished.progress.time / 60)}m`)
    $("#button_next").hide()
  } else if (response.status == "ok") {
    display_next_payload(response as DataPayload)
  } else {
    console.error("Non-ok response", response)
  }
}

$("#button_next").on("click", async function () {
  // check if all done
  for(let el of $(".span_toolbox_parent")) {
    console.log(el, $(el).css("display"))
    if ($(el).css("display") != "none") {
      notify("Please finish annotating all error spans before proceeding.")
      return
    }
  }
  // disable while communicating with the server
  $("#button_next").attr("disabled", "disabled")
  $("#button_next").val("Next 📶")
  action_log.push({ "time": Date.now() / 1000, "action": "submit" })
  await log_response({ "annotations": response_log, "actions": action_log })
  await load_next()
})

load_next()
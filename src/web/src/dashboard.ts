import { notify } from "./utils"
import $ from 'jquery';

let searchParams = new URLSearchParams(window.location.search)

let campaign_ids = searchParams.getAll("campaign_id")
let tokens = searchParams.getAll("token")

if (tokens.length != 0 && tokens.length != campaign_ids.length) {
    $("#main_div").html(`
        <div class="white-box">
        ⛔ Either no tokens should be provided or the same number as campaign IDs.
        </div>
    `)
    throw new Error("Mismatched number of tokens and campaign IDs")
}

function delta_to_human(delta: number): string {
    if (delta < 60) {
        return `${Math.round(delta)}s`
    } else if (delta < 60 * 60) {
        return `${Math.round(delta / 60)}m`
    } else if (delta < 60 * 60 * 24) {
        return `${Math.round(delta / 60 / 60)}h`
    } else {
        return `${Math.round(delta / 60 / 60 / 24)}d`
    }
}

campaign_ids.forEach(async (campaign_id, i) => {
    let token = tokens[i] || null
    try {
        await $.ajax({
            url: `/dashboard-data`,
            method: "POST",
            data: JSON.stringify({ "campaign_id": campaign_id, "token": token }),
            contentType: "application/json",
            dataType: "json",
            success: (x) => {
                let data = x.data

                let html = ""
                html += `
                <table>
                    <thead><tr>
                        <th style="min-width: 300px;">User ID</th>
                        <th style="min-width: 50px;">Progress</th>
                        <th style="min-width: 80px;">First</th>
                        <th style="min-width: 80px;">Last</th>
                        <th style="min-width: 80px;">Time</th>
                        <th style="min-width: 50px;">Actions</th>
                    </tr></thead>
                    <tbody>`
                for (let user_id in data) {
                    let status = ''
                    if (data[user_id]["progress"] == 0)
                        status = '💤'
                    else if (data[user_id]["progress"] == data[user_id]["total"])
                        status = '✅'
                    else
                        status = '🚧'

                    html += '<tr>'
                    html += `<td>${status} ${user_id}</td>`
                    html += `<td>${data[user_id]["progress"]}/${data[user_id]["total"]}</td>`
                    if (data[user_id]["time_start"] == null) {
                        html += `<td title="N/A"></td>`
                    } else {
                        html += `<td title="${new Date(data[user_id]["time_start"] * 1000).toLocaleString()}">${delta_to_human(Date.now() / 1000 - data[user_id]["time_start"])} ago</td>`
                    }
                    if (data[user_id]["time_end"] == null) {
                        html += `<td title="N/A"></td>`
                    } else {
                        html += `<td title="${new Date(data[user_id]["time_end"] * 1000).toLocaleString()}">${delta_to_human(Date.now() / 1000 - data[user_id]["time_end"])} ago</td>`
                    }
                    html += `<td>${Math.round(data[user_id]["time"] / 60)}m</td>`
                    html += `<td>
                        <a href="${data[user_id]["url"]}">🔗</a>
                        &nbsp;&nbsp;
                        <span class="reset-task" user_id="${user_id}" ${token == null ? "disabled" : ""}>🗑️</span>
                    </td>`
                    html += '</tr>'
                }
                html += '</tbody></table>'
                let dashboard_url = `${window.location.origin}/dashboard.html?campaign_id=${encodeURIComponent(campaign_id)}${token != null ? `&token=${encodeURIComponent(token)}` : ''}`
                let el = $(`
                    <div class="white-box">
                    <h3>${campaign_id} <a href="${dashboard_url}">🔗</a></h3>
                    ${html}
                    </div>`)

                $("#dashboard_div").append(el)
                if (token != null) {
                    $(".reset-task").on("click", function () {
                        let user_id = $(this).attr("user_id")
                        $.ajax({
                            url: `/reset-task`,
                            method: "POST",
                            data: JSON.stringify({ "campaign_id": campaign_id, "user_id": user_id, "token": token }),
                            contentType: "application/json",
                            dataType: "json",
                            success: (x) => {
                                notify(`Task for user ${user_id} has been reset.`)
                                location.reload()
                            },
                            error: (XMLHttpRequest, textStatus, errorThrown) => {
                                notify("Error resetting task:" + JSON.stringify(textStatus) + JSON.stringify(errorThrown));
                            },
                        });
                    })
                }
            },
            error: (XMLHttpRequest, textStatus, errorThrown) => {
                notify("Error fetching data:" + JSON.stringify(textStatus) + JSON.stringify(errorThrown));
            },
        });
    } catch (e) {
        notify("Error in try-catch: " + e);
    }
});


// progress requries an access token
if (tokens.length == 0) {
    $("#download_progress").attr("disabled", "true")
} else {
    $("#download_progress").attr("href", `/download-progress?${campaign_ids.map((id, i) => `campaign_id=${encodeURIComponent(id)}}`).join('&')}`)
}
$("#download_annotations").attr("href", `/download-annotations?${campaign_ids.map((id, i) => `campaign_id=${encodeURIComponent(id)}&${tokens[i] ? `token=${encodeURIComponent(tokens[i])}` : ''}`).join('&')}`)
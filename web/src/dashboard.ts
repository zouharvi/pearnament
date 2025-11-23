import { notify } from "./utils"
import $ from 'jquery';

let searchParams = new URLSearchParams(window.location.search)

let server_url = searchParams.get("server_url")
let campaign_ids = searchParams.getAll("campaign_id")
let tokens = searchParams.getAll("token")

if (tokens.length != 0 && tokens.length != campaign_ids.length) {
    notify("Either no tokens should be provided or the same number as campaign IDs")
    throw new Error("Mismatched number of tokens and campaign IDs")
}

function delta_to_human(delta: number): string {
    if (delta < 60) {
        return `${Math.round(delta)}s`
    } else if (delta < 60*60) {
        return `${Math.round(delta/60)}m`
    } else if (delta < 60*60*24) {
        return `${Math.round(delta/60/60)}h`
    } else  {
        return `${Math.round(delta/60/60/24)}d`
    }
}

campaign_ids.forEach(async (campaign_id, i) => {
    let token = tokens[i] || null
    try {
        await $.ajax({
            url: `${server_url}/dashboard-data`,
            method: "POST",
            data: JSON.stringify({ "campaign_id": campaign_id, "token": token }),
            contentType: "application/json",
            dataType: "json",
            success: (x) => {
                let data = x.data
                
                let html = ""
                html += `
                <table class="table table-striped">
                    <thead><tr>
                        <th>User ID</th>
                        <th>Progress</th>
                        <th>First</th>
                        <th>Last</th>
                        <th>Time</th>
                        <th>Actions</th>
                    </tr></thead>
                    <tbody>`
                for (let line in data) {
                    let status = ''
                    if (data[line]["progress"] == 0)
                        status = '💤'
                    else if (data[line]["progress"] == data[line]["total"])
                        status = '✅'
                    else 
                        status = '🚧'

                    html += '<tr>'
                    html += `<td>${status} ${line}</td>`
                    html += `<td>${data[line]["progress"]}/${data[line]["total"]}</td>`
                    if (data[line]["time_start"] == null) {
                        html += `<td title="N/A"></td>`
                    } else {
                        html += `<td title="${new Date(data[line]["time_start"]*1000).toLocaleString()}">${delta_to_human(Date.now()/1000 - data[line]["time_start"])} ago</td>`
                    }
                    if (data[line]["time_end"] == null) {
                        html += `<td title="N/A"></td>`
                    } else {
                        html += `<td title="${new Date(data[line]["time_end"]*1000).toLocaleString()}">${delta_to_human(Date.now()/1000 - data[line]["time_end"])} ago</td>`
                    }
                    html += `<td>${Math.round(data[line]["time"]/60)}m</td>`
                    // TODO: turn into actions
                    html += `<td><a href="${data[line]["url"]}">🔗</a>&nbsp;&nbsp;🗑️</td>`
                    html += '</tr>'
                }
                html += '</tbody></table>'

                $("#dashboard_div").append(
                    `<div class="white-box"><h3>${campaign_id}</h3> ${html} </div>`)
            },
            error: (XMLHttpRequest, textStatus, errorThrown) => {
                notify("Error fetching data:" + textStatus + errorThrown);
            },
        });
    } catch (e) {
        notify("Error in try-catch: " + e);
      }
});
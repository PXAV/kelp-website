let end_reached = false
let dynamic_counter = 1
let delay_time = 0

const loading_amount = 12

const wrapper = document.querySelector(".row-plugins")
const loader = document.querySelector(".spinner-holder .spinner-border")

{
    load_plugins()
    document.addEventListener("scroll", _ => {
        if($(window).scrollTop() + $(window).height() > $(document).height() - 200){
            load_plugins()
        }
    })
}


const plugin_template = `
    <li class="list-group-item media row m-0">
        <a href="/plugins/plugin_uuid">
            <img class="mr-3" src="/plugins?icon=plugin_uuid" alt="plugin_name_picture">
        </a>
        <div class="media-body pt-1">
            <h5><a href="/plugins/plugin_uuid">plugin_name</a></h5>
            <p>plugin_short_description</p>
        </div>
        <div class="col-lg-5 col-md-12 p-0">
            <div>plugin_tags</div>
        </div>
    </li>
`
const new_plugin_button = `
    <li class="list-group-item media row m-0 card-btn-add">
        <a href="/plugins/new">
            <img class="mr-3" src="/static/img/cross.png" alt="plugin_name">
        </a>
        <div class="media-body pt-1">
            <h5><a href="/plugins/new">Add Plugin</a><small></h5>
            <p>Create a new plugin</p>
        </div>
    </li>
`


function load_plugins(){
    function makeTagList(tags){
        let tag_list = tags.split(",")
        let output = ""
        for (let tag of tag_list){
            output += `<span class="badge badge-info m-1">${tag}</span>`
        }
        return output
    }
    if(new Date().getTime() > delay_time + 1000 && !end_reached) {
        loader.hidden = false
        delay_time = new Date().getTime()
        $.ajax({
            url: `/user?get_plugins&page=${dynamic_counter}&amount=${loading_amount}`,
            success: (response) => {
                if (response.data.length === 0){
                    wrapper.innerHTML = "<div class='text-center w-100 mt-3'><h6>You have not created any plugins, yet.</h6></div>"
                }
                {
                    let elem = document.querySelector(".card-btn-add")
                    if (!elem) {
                        wrapper.innerHTML += new_plugin_button
                    }
                }
                for (let plugin of response.data) {
                    wrapper.innerHTML += plugin_template
                        .replaceAll("plugin_name", plugin.plugin_name)
                        .replaceAll("plugin_short_description", plugin.short_description)
                        .replaceAll("plugin_uuid", plugin.uuid)
                        .replaceAll("plugin_tags", makeTagList(plugin.tags))
                }
                dynamic_counter += 1
                loader.hidden = true
            },
            error: (response) => {
                if(response.status === 404){
                    end_reached = true
                }
                loader.classList.remove("spinner-border")
                loader.innerHTML = "<span>End of content</span>"
            }
        })
    }
}
import modules.scripts as scripts
import gradio as gr
import os
from io import BytesIO
import requests
import json
from modules import script_callbacks
import base64

# global vars
wallet_address = ""
collections_and_slugs = {}

# Function to display UI components inside a tab
def on_ui_tabs():
    # Initializing UI components
    with gr.Blocks(analytics_enabled=False) as ui_component:
        with gr.Row():
            api_key_input = gr.Textbox(
                label="API Key",
                info="You can get your API key from your generaitiv profile",
                lines=1,
                value="",
                type="password"
            )
        with gr.Row():
            save_btn = gr.Button(value="Get your collections")
        with gr.Row():
            image_input = gr.Image(
                label='Image Input',
                source="upload",
                type="pil"
            )
            with gr.Column():
                collection_name = gr.Dropdown(
                    None,
                    label="Collection",
                    # info="Choose the collection you want to list your art in",
                    value="Choose the collection you want to list your art in"
                )
                artwork_name = gr.Textbox(
                    label="Name",
                    info="Give your artwork a cool name!",
                    lines=1,
                    value="",
                )
                amount = gr.Textbox(
                    label="Number of tokens",
                    info="How many tokens do you want to create?",
                    lines=1,
                    value="",
                )

        with gr.Row():
            artwork_description = gr.Textbox(
                label="Description",
                info="Write a description for your art",
                lines=3,
                value="",
            )
            traits_input = gr.Textbox(
                label="Traits",
                info="Enter traits in this format - trait1 : value1, trait2 : value2",
                placeholder="type: 1/1, artist: John Doe",
                lines=3,
                value="",
            )

        with gr.Row():
            submit_btn = gr.Button(
                value="Creait token",
                variant="primary"
            )

            # invisible components
            upload_url = gr.Textbox(
                label="",
                info="",
                lines=1,
                value="",
                visible=False
            )
            img_str = gr.Textbox(
                label="",
                info="",
                lines=1,
                value="",
                visible=False
            )
            response = gr.Textbox(
                label="",
                info="",
                lines=1,
                value="",
                visible=False
            )
            image_path = gr.Textbox(
                label="",
                info="",
                lines=1,
                value="",
                visible=False
            )

        # onclick events
        save_btn.click(
            get_collections,
            inputs = [api_key_input],
            outputs = [collection_name],
        )

        # taking javascript code from a file and passing it as onlick function
        current_dir = os.getcwd()
        with open(os.path.join(current_dir, r'extensions/gai-eleven/javascript/uploadImage.js')) as dataFile:
            js_logic = dataFile.read()

        submit_btn.click(
            create_token,
            inputs = [api_key_input, save_btn, collection_name, artwork_name, amount, artwork_description, image_input, submit_btn, traits_input],
            outputs = [upload_url, img_str],
        ).success(
            fn=None,
            inputs = [upload_url, img_str],
            outputs = [response],
            _js=js_logic,
        )

        return [(ui_component, "Send to Generaitiv", "extension_template_tab")]


# Get a user's collections given api key
def get_collections(api_key_input):
    global wallet_address, collections_and_slugs

    wallet_address = requests.get(
        "https://api.generaitiv.xyz/v1/consumer/user-info/",
        headers={
            "Authorization": f"Bearer {api_key_input}",
            "Content-Type": "application/json"
        }
    )
    wallet_address = wallet_address.json()["address"]

    user_collections = requests.get(
        f'https://api.generaitiv.xyz/v1/u/{wallet_address}/collections',
        headers={
            "Authorization": f"Bearer {api_key_input}",
            "Content-Type": "application/json"
        }
    )

    for collection in user_collections.json()["collections"]:
        collections_and_slugs[collection["name"]] = collection["slugOrAddress"]

    return gr.Dropdown.update(choices=list(collections_and_slugs.keys()))


# function to create a token on generaitiv
def create_token(api_key_input, save_btn, collection_name, artwork_name, amount, artwork_description, image_input, submit_btn, traits_input):
    print("User Inputs: ")
    print("collection_name: ", collection_name)
    print("artwork_name: ", artwork_name)
    print("amount: ", amount)
    print("artwork_description: ", artwork_description)
    print("image input: ", image_input)
    print("traits input: ", traits_input)

    global wallet_address, collections_and_slugs

    traits_dict_temp = {i.split(':')[0]: i.split(':')[1] for i in traits_input.replace(" ", "").split(',')}

    attributes = []
    for key in traits_dict_temp.keys():
        temp = {}
        temp["trait_type"] = key
        temp["value"] = traits_dict_temp[key]
        attributes.append(temp)

    print("attributes: ", attributes)

    # Getting new token ID
    new_tokenid = requests.get(
        f'https://api.generaitiv.xyz/v1/c/virtual/next/{wallet_address}',
        headers={
            "Authorization": f"Bearer {api_key_input}",
            "Content-Type": "application/json"
        }
    )
    new_token_id = new_tokenid.json()["tokenId"]
    print("Obtained new token ID: ", new_token_id)
    print()

    # Creating token object
    token_obj = {
        "tokenId": new_token_id,
        "amount": "0x" + hex(int(amount))[2:].zfill(64),
        "attributes": attributes,
        "name": artwork_name,
        "description": artwork_description
    }
    print("Token Object: ")
    print(json.dumps(token_obj, indent=1))
    print()

    slug = collections_and_slugs[collection_name]

    # Creating token
    res = requests.post(
        f"https://api.generaitiv.xyz/v1/c/virtual/token/{slug}/{new_token_id}",
        json = token_obj,
        headers={
            "Authorization": f"Bearer {api_key_input}",
            "Content-Type": "application/json"
        }
    )
    print()
    print("Response: ", res.text)

    # Getting upload PUT url
    upload_puturl = requests.get(
        f'https://api.generaitiv.xyz/v1/upload/token/{new_token_id}/art.png',
        headers={
            "Authorization": f"Bearer {api_key_input}",
            "Content-Type": "application/json"
        }
    )
    upload_put_url = upload_puturl.json()["url"]

    # print(type(image_input))
    # image_input.save('art.png', 'PNG')
    if (image_input):
        buffered = BytesIO()
        image_input.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue())
        img_str = bytes("data:image/jpeg;base64,", encoding='utf-8') + img_str
        img_str = img_str.decode("utf-8")
    else:
        img_str = ""

    return [upload_put_url, img_str]

script_callbacks.on_ui_tabs(on_ui_tabs)

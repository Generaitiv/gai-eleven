// function to upload image to token
async function uploadImg(uploadUrl, imgBase64, flag) {
	if (flag == "false") {
		return [
			"Could not set your artwork to the created token. Please check if your input values are correct.",
		];
	} else {
		// finding file extension
		let fileExtension = imgBase64.substring(
			"data:image/".length,
			imgBase64.indexOf(";base64")
		);

		// function to convert base64 encoded string to blob (the image is passed to this function as a base64 string by gradio)
		function base64ImageToBlob(str, fileExtension) {
			var pos = str.indexOf(";base64,");
			var type = str.substring(5, pos);
			var b64 = str.substr(pos + 8);
			var imageContent = atob(b64);
			var buffer = new ArrayBuffer(imageContent.length);
			var view = new Uint8Array(buffer);

			for (var n = 0; n < imageContent.length; n++) {
				view[n] = imageContent.charCodeAt(n);
			}

			var blob = new File([buffer], `art.${fileExtension}`, { type: type });
			return blob;
		}

		let imgFile = base64ImageToBlob(imgBase64, fileExtension);

		// PUT request for uploading image using upload URL
		const response = await fetch(uploadUrl, {
			method: "PUT",
			body: imgFile,
		});

		return ["Token created successfully!"];
	}
}

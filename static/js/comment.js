document.addEventListener('submit', function (event) {
    if (event.target.matches('.add-comment')) {
        event.preventDefault();
        const postID = event.target.getAttribute('data-post-id');
        const commentInput = event.target.querySelector('input[name="comment"]').value;

        fetch('/addComment/' + postID + '/' + constant.uid, {
            method: 'POST',
            body: new URLSearchParams({ 'comment': commentInput }),
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
        })
            .then(response => response.json())
            .then(data => {
                const commentData = data.new_comment;
                const commentsSection = document.getElementById('comments_' + postID);

                // Construct the HTML structure for the new comment and commenter info
                const newCommentHTML = `
            <div class="user-profile">
                <img class="user-image"
                    src="{% if commentData.commenter_info.thumbnail %}{{ commentData.commenter_info.thumbnail }}{% else %}/static/images/profile.png{% endif %}"
                    alt="User">
                <p>${commentData.commenter_info.name}</p>
            </div>
            <div class="comment">
                <p>${commentData.comment}</p>
                <span>${commentData.time}</span>
            </div>
        `;

                commentsSection.innerHTML += newCommentHTML;
            })
            .catch(error => {
                console.error('Error:', error);
            });
    }
});
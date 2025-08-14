// QA 데이터를 저장할 변수
let qaData = null;

// QA 데이터를 API에서 가져와 qaData에 저장하는 함수
async function loadQAData() {
    const urlParams = new URLSearchParams(window.location.search);
    const id = urlParams.get("id");

    if (id) {
        try {
            const response = await fetch(`/api/qas/${id}`);
            if (response.ok) {
                qaData = await response.json(); // 데이터를 qaData 변수에 저장
                
                // 비밀글이 아닌 경우에만 비밀번호 확인
                if (!qaData.hidden) {
                    showPasswordModal(id);
                } else {
                    // 비밀글인 경우 바로 폼 채우기 (이미 detail에서 확인했음)
                    populateFormFields();
                    setRedirectUrl();
                }
            } else {
                alert("글을 불러오는 데 실패했습니다.");
                history.back();
            }
        } catch (error) {
            console.error("Error fetching QA:", error);
            alert("서버와 통신 중 문제가 발생했습니다.");
            history.back();
        }
    }
}

// redirect_url 설정 함수
function setRedirectUrl() {
    const redirectUrlInput = document.getElementById("redirect_url");
    redirectUrlInput.value = qaData.qa_type === "CUSTOMER" ? "/qa" : "/lost";
}

// 비밀번호 확인 모달을 표시하는 함수 (비밀글이 아닌 경우)
function showPasswordModal(id) {
    // 비밀번호 입력 모달 HTML을 동적으로 생성
    const modalHtml = `
        <div class="modal fade" id="passwordModal" tabindex="-1" aria-hidden="true">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">비밀번호 확인</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <label for="passwordInput" class="form-label">글 작성 시 입력한 비밀번호를 입력해주세요</label>
                        <input type="password" class="form-control" id="passwordInput" placeholder="비밀번호">
                        <div id="passwordError" class="text-danger mt-2" style="display: none;"></div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">취소</button>
                        <button type="button" class="btn btn-primary" id="confirmPasswordBtn">확인</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // 모달을 body에 추가
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    const passwordModal = new bootstrap.Modal(document.getElementById('passwordModal'));
    
    let passwordVerified = false;
    
    // 모달이 닫힐 때 뒤로가기 (비밀번호 확인 성공한 경우 제외)
    document.getElementById('passwordModal').addEventListener('hidden.bs.modal', function () {
        if (!passwordVerified) {
            history.back();
        }
    });
    
    // 확인 버튼 클릭 이벤트
    document.getElementById('confirmPasswordBtn').addEventListener('click', async function() {
        const password = document.getElementById('passwordInput').value.trim();
        const passwordError = document.getElementById('passwordError');
        
        if (!password) {
            passwordError.textContent = "비밀번호를 입력해주세요.";
            passwordError.style.display = "block";
            return;
        }
        
        try {
            const response = await fetch(`/api/qas/${id}/check_password?password=${encodeURIComponent(password)}`);
            
            if (response.ok) {
                // 비밀번호 확인 성공 - 플래그 설정 후 모달 닫고 폼 채우기
                passwordVerified = true;
                passwordModal.hide();
                populateFormFields();
                setRedirectUrl();
            } else {
                // 비밀번호 확인 실패
                passwordError.textContent = "비밀번호가 일치하지 않습니다.";
                passwordError.style.display = "block";
                document.getElementById('passwordInput').value = "";
                document.getElementById('passwordInput').focus();
            }
        } catch (error) {
            console.error("Password verification error:", error);
            passwordError.textContent = "서버와 통신 중 문제가 발생했습니다.";
            passwordError.style.display = "block";
        }
    });
    
    // Enter 키 이벤트
    document.getElementById('passwordInput').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            document.getElementById('confirmPasswordBtn').click();
        }
    });
    
    passwordModal.show();
}

// 폼 필드에 데이터를 채워 넣는 함수
function populateFormFields() {
    if (!qaData) return; // qaData가 없으면 중단

    const quill = new Quill('#editor', {theme: 'snow'});

    // Quill 에디터 초기 내용 설정 및 높이 조정
    quill.root.innerHTML = qaData.content || '';
    adjustQuillHeight();

    document.getElementById("writer").value = qaData.writer;
    document.getElementById("email").value = qaData.email || '';
    document.getElementById("title").value = qaData.title;
    document.getElementById("password").value = qaData.password;

    // Display the attachment name and preview if exists
    if (qaData.attachment_filename) {
        document.getElementById("attachmentName").textContent = `기존 첨부 파일: ${qaData.attachment_filename}`;
        document.getElementById("keepAttachment").value = "true";
        document.getElementById("removeAttachment").classList.remove("d-none");

        if (qaData.attachment && /\.(jpg|jpeg|png|gif)$/i.test(qaData.attachment_filename)) {
            const attachmentPreview = document.createElement("img");
            attachmentPreview.src = `data:image/png;base64,${qaData.attachment}`;
            attachmentPreview.alt = qaData.attachment_filename;
            attachmentPreview.style.maxWidth = "100%";
            attachmentPreview.style.marginTop = "10px";
        }
    }

    document.getElementById("hidden").checked = qaData.hidden;

    // Quill 내용이 변경될 때마다 높이 자동 조정
    quill.on('text-change', adjustQuillHeight);
}

// Quill 높이 동적으로 조정 함수
function adjustQuillHeight() {
    const editorContainer = document.getElementById("editor");
    const contentHeight = editorContainer.scrollHeight;
    editorContainer.style.height = `${Math.max(contentHeight, 200)}px`; // 최소 200px 유지
}

// 파일 선택 시 파일 이름 표시 업데이트 및 keepAttachment 설정 제거
document.getElementById("attachment").addEventListener("change", (event) => {
    document.getElementById("attachmentName").textContent = event.target.files.length ? `첨부 파일: ${event.target.files[0].name}` : "선택된 파일 없음";
    document.getElementById("keepAttachment").value = event.target.files.length ? "false" : "true";
    document.getElementById("removeAttachment").classList.add("d-none");
});

// 첨부파일 삭제 버튼 클릭 이벤트
document.getElementById("removeAttachment").addEventListener("click", () => {
    document.getElementById("attachment").value = "";
    document.getElementById("attachmentName").textContent = "선택된 파일 없음";
    document.getElementById("keepAttachment").value = "false";
    document.getElementById("removeAttachment").classList.add("d-none");
    document.getElementById("attachmentPreviewContainer").innerHTML = "";
});

// 폼 제출 시 서버에 수정 요청 보내기
document.getElementById("qaForm").addEventListener("submit", async function (event) {
    event.preventDefault();

    const urlParams = new URLSearchParams(window.location.search);
    const id = urlParams.get("id");

    const formData = new FormData(this);
    formData.append("content", document.querySelector("#editor .ql-editor").innerHTML);

    try {
        const response = await fetch(`/api/qas/${id}`, {
            method: "PATCH",
            body: formData
        });

        if (response.ok) {
            alert("글이 성공적으로 수정되었습니다.");
            window.location.href = formData.get("redirect_url");
        } else {
            alert("글 수정에 실패했습니다.");
        }
    } catch (error) {
        console.error("Error updating QA:", error);
        alert("서버 오류가 발생했습니다. 다시 시도해주세요.");
    }
});

// 페이지 로드 시 QA 데이터 로드
document.addEventListener("DOMContentLoaded", function () {
    loadQAData();
});

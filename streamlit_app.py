import os, sqlite3, secrets
from pathlib import Path
from datetime import datetime
import streamlit as st

DB = Path(os.getenv("BOOKSTORE_DB_PATH", str(Path(__file__).parent / "chaekirang.db")))
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "change-this-admin-password")
EMAIL_DOMAIN = os.getenv("SCHOOL_EMAIL_DOMAIN", "").strip().lower().lstrip("@")
ACCESS_CODE = os.getenv("SCHOOL_ACCESS_CODE", "")
st.set_page_config(page_title="책이랑 | 학교협동조합 중고서점", page_icon="📚", layout="wide")

def connect():
    c=sqlite3.connect(DB, check_same_thread=False); c.row_factory=sqlite3.Row; return c
def init():
    with connect() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS books(id INTEGER PRIMARY KEY, title TEXT NOT NULL, author TEXT DEFAULT '', publisher TEXT DEFAULT '', category TEXT DEFAULT '기타', condition TEXT DEFAULT '좋음', price INTEGER NOT NULL, stock INTEGER NOT NULL DEFAULT 1, description TEXT DEFAULT '', cover TEXT DEFAULT '', active INTEGER DEFAULT 1, created TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS orders(id INTEGER PRIMARY KEY, code TEXT UNIQUE, email TEXT, name TEXT, items TEXT, total INTEGER, fulfillment TEXT, address TEXT, phone TEXT, status TEXT DEFAULT '결제 대기', created TEXT);
        """)
        if c.execute("SELECT COUNT(*) FROM books").fetchone()[0]==0:
            now=datetime.now().isoformat(timespec="minutes")
            c.executemany("INSERT INTO books(title,author,publisher,category,condition,price,stock,description,cover,active,created) VALUES(?,?,?,?,?,?,?,?,?,?,?)",[
            ("청소년을 위한 경제 수업","홍길동","배움출판","경제","매우 좋음",8000,3,"개념 이해에 좋은 입문서입니다.","",1,now),
            ("과학으로 보는 세상","김과학","푸른책","과학","좋음",6500,2,"검수를 마친 중고 도서입니다.","",1,now),
            ("생각하는 글쓰기","이작가","학교책방","문학","보통",4000,4,"사용감이 있으나 읽는 데 문제 없습니다.","",1,now)])
def won(n): return f"{int(n):,}원"
def style():
    st.markdown("""<style>
    .stApp{background:#fbfaf7;color:#242424} h1,h2,h3,p,label{color:#242424}
    .brand{font-size:2.2rem;font-weight:850;letter-spacing:-1px;color:#242424}
    .brand span{color:#d9682b}.muted{color:#666;font-size:.9rem}
    .booktitle{font-size:1.02rem;font-weight:750;color:#222;line-height:1.4}
    .price{font-size:1.18rem;font-weight:850;color:#c6531e}
    div.stButton>button[kind=primary]{background:#d9682b;border-color:#d9682b}
    </style>""",unsafe_allow_html=True)
    st.markdown('<div class="brand"><span>책</span>이랑</div><p class="muted">학교협동조합이 직접 매입·검수·판매하는 우리 학교 중고책 서점</p>',unsafe_allow_html=True)
    st.divider()
def login():
    st.subheader("학교 구성원 확인")
    with st.form("login"):
        email=st.text_input("학교 이메일",placeholder="student@school.ac.kr")
        name=st.text_input("이름")
        code=st.text_input("학교 구성원 확인 코드(학교에서 받은 경우)",type="password")
        ok=st.form_submit_button("시작하기",type="primary")
    if ok:
        email=email.strip().lower()
        if "@" not in email: st.error("올바른 이메일 주소를 입력해 주세요.")
        elif EMAIL_DOMAIN and not email.endswith("@"+EMAIL_DOMAIN): st.error(f"학교 이메일(@{EMAIL_DOMAIN})을 사용해 주세요.")
        elif ACCESS_CODE and not secrets.compare_digest(code,ACCESS_CODE): st.error("확인 코드가 올바르지 않습니다.")
        else:
            st.session_state.member={"email":email,"name":name.strip() or email.split("@")[0]}
            st.rerun()
    if not EMAIL_DOMAIN and not ACCESS_CODE: st.info("개발 모드입니다. 실제 운영 전 학교 인증 설정이 필요합니다.")
def catalog():
    st.subheader("도서 둘러보기")
    a,b=st.columns([3,1])
    search=a.text_input("도서명·저자·출판사 검색",placeholder="찾는 책을 검색하세요")
    with connect() as c: cats=["전체"]+[r[0] for r in c.execute("SELECT DISTINCT category FROM books WHERE active=1 ORDER BY category")]
    cat=b.selectbox("분류",list(dict.fromkeys(cats)))
    sql="SELECT * FROM books WHERE active=1 AND stock>0"; args=[]
    if search: sql+=" AND (title LIKE ? OR author LIKE ? OR publisher LIKE ?)"; args += [f"%{search}%"]*3
    if cat!="전체": sql+=" AND category=?"; args.append(cat)
    with connect() as c: rows=c.execute(sql+" ORDER BY id DESC",args).fetchall()
    if not rows: st.info("조건에 맞는 도서가 없습니다."); return
    cols=st.columns(3)
    for i,p in enumerate(rows):
        with cols[i%3]:
            with st.container(border=True):
                if p["cover"]: st.image(p["cover"],width=150)
                else: st.markdown("### 📚")
                st.markdown(f'<div class="booktitle">{p["title"]}</div><div class="muted">{p["author"]} · {p["publisher"]}</div><div class="muted">상태: {p["condition"]} · 재고 {p["stock"]}권</div><div class="price">{won(p["price"])}</div>',unsafe_allow_html=True)
                if p["description"]: st.caption(p["description"])
                if st.button("장바구니 담기",key=f"add{p['id']}",use_container_width=True):
                    cart=st.session_state.setdefault("cart",{}); cart[str(p["id"])]=cart.get(str(p["id"]),0)+1; st.success("담았습니다.")
def checkout():
    st.subheader("장바구니 및 주문")
    cart=st.session_state.setdefault("cart",{})
    if not cart: st.info("장바구니가 비어 있습니다."); return
    with connect() as c:
        ids=[int(k) for k in cart]
        ps={str(r["id"]):r for r in c.execute(f"SELECT * FROM books WHERE id IN ({','.join('?'*len(ids))})",ids).fetchall()}
    total=0
    for pid in list(cart):
        p=ps.get(pid)
        if not p: del cart[pid]; continue
        a,b,d=st.columns([4,1,1]); a.write(p["title"])
        q=b.number_input("수량",1,max(1,p["stock"]),min(cart[pid],max(1,p["stock"])),key="q"+pid)
        cart[pid]=q; total+=p["price"]*q; d.write(won(p["price"]*q))
    st.markdown(f"### 합계: {won(total)}")
    with st.form("checkout"):
        how=st.radio("수령 방법",["학교에서 수령","택배 배송"],horizontal=True)
        phone=st.text_input("연락처"); address=st.text_area("배송 주소 (택배 선택 시 필수)")
        st.warning("현재는 주문 접수 데모입니다. 실제 온라인 결제는 PG사 연동 후 활성화해야 합니다.")
        submit=st.form_submit_button("주문 접수",type="primary")
    if submit:
        if not phone.strip(): st.error("연락처를 입력해 주세요.")
        elif how=="택배 배송" and not address.strip(): st.error("배송 주소를 입력해 주세요.")
        else:
            import json
            items=[]; total=0
            with connect() as c:
                for pid,q in cart.items():
                    p=c.execute("SELECT * FROM books WHERE id=? AND active=1",(int(pid),)).fetchone()
                    if not p or p["stock"]<q: st.error("재고가 부족합니다. 장바구니를 확인해 주세요."); return
                    items.append({"title":p["title"],"price":p["price"],"quantity":q}); total+=p["price"]*q
                code="BK-"+secrets.token_hex(4).upper(); m=st.session_state.member
                c.execute("INSERT INTO orders(code,email,name,items,total,fulfillment,address,phone,status,created) VALUES(?,?,?,?,?,?,?,?,?,?)",(code,m["email"],m["name"],json.dumps(items,ensure_ascii=False),total,how,address.strip(),phone.strip(),"결제 대기",datetime.now().isoformat(timespec="minutes")))
            st.session_state.cart={}; st.success(f"주문 접수 완료: {code}"); st.info("결제 승인 전 상태입니다. 실제 운영 전 결제대행사 연동이 필요합니다.")
def my_orders():
    st.subheader("내 주문")
    with connect() as c: rows=c.execute("SELECT * FROM orders WHERE email=? ORDER BY id DESC",(st.session_state.member["email"],)).fetchall()
    if not rows: st.info("주문 내역이 없습니다.")
    for o in rows:
        with st.container(border=True):
            st.markdown(f"**{o['code']}** · {won(o['total'])} · {o['status']}")
            st.caption(f"{o['created'][:16]} · {o['fulfillment']}")
            st.write(o["items"])
def admin():
    st.subheader("협동조합 관리자")
    if not st.session_state.get("admin"):
        with st.form("admin"):
            pw=st.text_input("관리자 비밀번호",type="password"); go=st.form_submit_button("로그인")
        if go:
            if secrets.compare_digest(pw,ADMIN_PASSWORD): st.session_state.admin=True; st.rerun()
            else: st.error("비밀번호가 올바르지 않습니다.")
        return
    t1,t2=st.tabs(["도서 등록·재고","주문 관리"])
    with t1:
        with st.form("newbook",clear_on_submit=True):
            title=st.text_input("도서명*"); author=st.text_input("저자"); publisher=st.text_input("출판사")
            category=st.selectbox("분류",["교재","문학","인문","과학","경제","어학","기타"])
            condition=st.selectbox("상태",["최상","매우 좋음","좋음","보통"])
            price=st.number_input("판매가(원)",0,step=500,value=5000); stock=st.number_input("재고",0,step=1,value=1)
            cover=st.text_input("표지 이미지 URL(선택)"); desc=st.text_area("설명/검수 메모")
            save=st.form_submit_button("도서 등록",type="primary")
        if save:
            if not title.strip(): st.error("도서명을 입력하세요.")
            else:
                with connect() as c: c.execute("INSERT INTO books(title,author,publisher,category,condition,price,stock,description,cover,active,created) VALUES(?,?,?,?,?,?,?,?,?,1,?)",(title,author,publisher,category,condition,int(price),int(stock),desc,cover,datetime.now().isoformat(timespec="minutes")))
                st.success("등록했습니다."); st.rerun()
        with connect() as c: rows=c.execute("SELECT * FROM books ORDER BY id DESC").fetchall()
        for p in rows:
            with st.expander(f"{p['title']} · {won(p['price'])} · 재고 {p['stock']}"):
                with st.form(f"edit{p['id']}"):
                    price2=st.number_input("가격",0,value=p["price"],step=500,key=f"p{p['id']}")
                    stock2=st.number_input("재고",0,value=p["stock"],key=f"s{p['id']}")
                    active=st.checkbox("판매 중",bool(p["active"]),key=f"a{p['id']}")
                    save2=st.form_submit_button("저장")
                if save2:
                    with connect() as c: c.execute("UPDATE books SET price=?,stock=?,active=? WHERE id=?",(price2,stock2,int(active),p["id"]))
                    st.rerun()
    with t2:
        with connect() as c: rows=c.execute("SELECT * FROM orders ORDER BY id DESC").fetchall()
        for o in rows:
            with st.expander(f"{o['code']} · {o['name']} · {won(o['total'])} · {o['status']}"):
                st.write(f"{o['email']} · {o['phone']} · {o['fulfillment']} · {o['address']}")
                st.write(o["items"])
                status=st.selectbox("상태",["결제 대기","결제 완료","상품 준비 중","수령 가능","배송 중","완료","취소"],key=f"status{o['id']}")
                if st.button("상태 변경",key=f"save{o['id']}"):
                    with connect() as c: c.execute("UPDATE orders SET status=? WHERE id=?",(status,o["id"]))
                    st.rerun()
def main():
    init(); style()
    if "member" not in st.session_state: login(); return
    a,b=st.columns([4,1]); a.caption(f"이용자: {st.session_state.member['name']} · {st.session_state.member['email']}")
    if b.button("로그아웃"): st.session_state.clear(); st.rerun()
    t1,t2,t3,t4=st.tabs(["도서 둘러보기","장바구니·주문","내 주문","관리자"])
    with t1: catalog()
    with t2: checkout()
    with t3: my_orders()
    with t4: admin()
    st.divider(); st.caption("책이랑은 학교협동조합 직접 매입·검수·판매 방식입니다. 입점 사업자·정액제 콘텐츠·쿠폰·마일리지는 제공하지 않습니다.")
if __name__=="__main__": main()

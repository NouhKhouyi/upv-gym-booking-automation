from upv_gym_booking.client import find_reservation_links, is_session_registered


def test_find_reservation_links_keeps_requested_order_and_normalizes_urls() -> None:
    html = """
    <html>
      <body>
        <a class="upv_enlacelista" href="sic_depact.Reserva?p=024">MUS024 tarde</a>
        <a class="upv_enlacelista" href="/pls/soalu/sic_depact.Reserva?p=009">MUS009 manana</a>
        <a class="upv_enlacelista" href="sic_depact.Reserva?p=999">MUS999 fuera de objetivo</a>
      </body>
    </html>
    """

    links = find_reservation_links(html, ("009", "024"))

    assert [link.session_code for link in links] == ["009", "024"]
    assert links[0].url == "https://intranet.upv.es/pls/soalu/sic_depact.Reserva?p=009"
    assert links[1].url == "https://intranet.upv.es/pls/soalu/sic_depact.Reserva?p=024"


def test_find_reservation_links_ignores_duplicate_codes() -> None:
    html = """
    <a class="upv_enlacelista" href="first">MUS009 primer hueco</a>
    <a class="upv_enlacelista" href="second">MUS009 duplicado</a>
    """

    links = find_reservation_links(html, ("MUS009",))

    assert len(links) == 1
    assert links[0].url.endswith("/first")


def test_find_reservation_links_matches_plain_numeric_code_in_label() -> None:
    html = """
    <a class="upv_enlacelista" href="sic_depact.HSemActMatri?p=45">Turno 045 - reservar</a>
    """

    links = find_reservation_links(html, ("045",))

    assert len(links) == 1
    assert links[0].session_code == "045"


def test_find_reservation_links_supports_new_hsemactmatri_selector_without_class() -> None:
    html = """
    <a href="sic_depact.HSemActMatri?p_campus=V&p_codacti=21809&p_codgrupo_mat=ABC&p_tipoact=6846">
      MUS045 reserva
    </a>
    """

    links = find_reservation_links(html, ("045",))

    assert len(links) == 1
    assert "HSemActMatri" in links[0].url


def test_find_reservation_links_matches_code_from_table_row() -> None:
    html = """
    <table>
      <tr>
        <td>MUSCULACION 045</td>
        <td>19:00</td>
        <td>
          <a href="sic_depact.HSemActMatri?p_codgrupo_mat=ABC">
            Inscribirse
          </a>
        </td>
      </tr>
    </table>
    """

    links = find_reservation_links(html, ("045",))

    assert len(links) == 1
    assert links[0].session_code == "045"
    assert "codgrupo_mat=ABC" in links[0].url


def test_find_reservation_links_uses_matching_cell_when_row_has_multiple_links() -> None:
    html = """
    <table>
      <tr>
        <td>MUS045 <a href="sic_depact.HSemActMatri?p_codgrupo_mat=AAA">Inscribirse</a></td>
        <td>MUS060 <a href="sic_depact.HSemActMatri?p_codgrupo_mat=BBB">Inscribirse</a></td>
        <td>MUS075 <a href="sic_depact.HSemActMatri?p_codgrupo_mat=CCC">Inscribirse</a></td>
      </tr>
    </table>
    """

    links = find_reservation_links(html, ("060",))

    assert len(links) == 1
    assert "codgrupo_mat=BBB" in links[0].url


def test_find_reservation_links_does_not_use_cancel_links() -> None:
    html = """
    <table>
      <tr>
        <td>MUSCULACION 071</td>
        <td>
          <a class="upv_enlacelista" href="sic_depact.HSemActDesMat?p_codgrupo_desmat=ABC">
            Cancelar inscripcion
          </a>
        </td>
      </tr>
    </table>
    """

    assert find_reservation_links(html, ("071",)) == []


def test_is_session_registered_detects_already_inscribed_cell() -> None:
    html = """
    <table>
      <tr>
        <td>17:30-18:30</td>
        <td>MUS071 Already inscribed</td>
      </tr>
    </table>
    """

    assert is_session_registered(html, "071") is True


def test_is_session_registered_detects_cancel_link_in_registered_row() -> None:
    html = """
    <table>
      <tr>
        <td>MUSCULACION 045 Friday Confirmed</td>
        <td>
          <a href="sic_depact.HSemActDesMat?p_codgrupo_desmat=ABC">
            Cancel registration
          </a>
        </td>
      </tr>
    </table>
    """

    assert is_session_registered(html, "045") is True


def test_is_session_registered_does_not_treat_full_as_registered() -> None:
    html = """
    <table>
      <tr>
        <td>21:30-22:30</td>
        <td>MUS045 Only Partners Full</td>
      </tr>
    </table>
    """

    assert is_session_registered(html, "045") is False

"""Polar geometry, rounded slice paths, concentric rings, cascading radial tiers, and hit testing matching the launcher HUD."""

import math
from typing import Optional, Tuple
from PyQt6.QtCore import QPointF, QRectF
from PyQt6.QtGui import QPainterPath


class DonutGeometry:
    """
    Calculates polar coordinates, slice paths, inner ring buttons,
    satellite orbits, cascading concentric radial arc tiers, and precise polar hit testing.
    """

    def __init__(
        self,
        hub_radius: float = 56.0,
        inner_ring_r1: float = 62.0,
        inner_ring_r2: float = 95.0,
        outer_ring_r1: float = 100.0,
        outer_ring_r2: float = 175.0,
        disc_radius: float = 186.0,
        sub_ring_r1: float = 182.0,
        sub_ring_r2: float = 265.0,
        center_x: float = 290.0,
        center_y: float = 300.0
    ):
        self.hub_radius = hub_radius
        self.inner_ring_r1 = inner_ring_r1
        self.inner_ring_r2 = inner_ring_r2
        self.inner_radius = outer_ring_r1
        self.outer_radius = outer_ring_r2
        self.disc_radius = disc_radius
        self.sub_ring_r1 = sub_ring_r1
        self.sub_ring_r2 = sub_ring_r2
        self.center_x = center_x
        self.center_y = center_y

        # Satellite buttons: 3 clean circular buttons orbiting top-left shoulder (Explorer, Copy Path, Close)
        # Generous radius for flawless clearance from all liquid bulges
        self.satellite_angles = [-152.0, -135.0, -118.0]
        self.satellite_orbit_r = self.disc_radius + 24.0
        self.satellite_btn_r = 13.0

        # Inner ring utility buttons: 6 evenly spaced positions
        self.inner_button_count = 6
        self.inner_orbit_r = (self.inner_ring_r1 + self.inner_ring_r2) / 2.0

    def get_satellite_pos(self, index: int) -> QPointF:
        """Get center point of a satellite button."""
        if 0 <= index < len(self.satellite_angles):
            angle_rad = math.radians(self.satellite_angles[index])
            x = self.center_x + self.satellite_orbit_r * math.cos(angle_rad)
            y = self.center_y + self.satellite_orbit_r * math.sin(angle_rad)
            return QPointF(x, y)
        return QPointF(self.center_x, self.center_y)

    def get_inner_button_pos(self, index: int) -> QPointF:
        """Get center point of an inner ring utility button."""
        span = 360.0 / self.inner_button_count
        angle_rad = math.radians(-90.0 + index * span)
        x = self.center_x + self.inner_orbit_r * math.cos(angle_rad)
        y = self.center_y + self.inner_orbit_r * math.sin(angle_rad)
        return QPointF(x, y)

    def get_annular_sector_path(
        self,
        cx: float,
        cy: float,
        a_start_deg: float,
        a_end_deg: float,
        r_in: float,
        r_out: float,
        gap_deg: float = 2.5,
        corner_r: float = 6.0,
        convex_bulge: float = 0.0
    ) -> QPainterPath:
        """Create a rounded annular curved sector path with organic liquid surface tension bulge."""
        a1 = a_start_deg + gap_deg / 2.0
        a2 = a_end_deg - gap_deg / 2.0
        if a2 <= a1 or r_out <= r_in + 4.0:
            return QPainterPath()

        cr = min(corner_r, (r_out - r_in) * 0.30)
        d_out = math.degrees(cr / max(1.0, r_out))
        d_in = math.degrees(cr / max(1.0, r_in))

        rad1_x = math.cos(math.radians(a1))
        rad1_y = math.sin(math.radians(a1))
        rad2_x = math.cos(math.radians(a2))
        rad2_y = math.sin(math.radians(a2))

        p_in_start = r_in + cr * 0.85
        p_out_start = r_out - cr * 0.85

        a_out_start = a1 + d_out
        a_out_end = a2 - d_out
        a_in_start = a1 + d_in
        a_in_end = a2 - d_in

        path = QPainterPath()
        ptA = QPointF(cx + p_in_start * rad1_x, cy + p_in_start * rad1_y)
        ptB = QPointF(cx + p_out_start * rad1_x, cy + p_out_start * rad1_y)
        ptC_ctrl = QPointF(cx + r_out * rad1_x, cy + r_out * rad1_y)
        ptD = QPointF(cx + r_out * math.cos(math.radians(a_out_start)), cy + r_out * math.sin(math.radians(a_out_start)))

        path.moveTo(ptA)
        path.lineTo(ptB)
        path.quadTo(ptC_ctrl, ptD)

        if convex_bulge > 0.5:
            # Organic liquid meniscus bulge: center crests smoothly outward like a fluid drop
            mid_a = (a_out_start + a_out_end) / 2.0
            mid_rad = math.radians(mid_a)
            crest_r = r_out + convex_bulge

            ctrl1_a = a_out_start + (mid_a - a_out_start) * 0.50
            ctrl2_a = a_out_end - (a_out_end - mid_a) * 0.50
            ctrl_r = r_out + convex_bulge * 0.72

            c1 = QPointF(cx + ctrl_r * math.cos(math.radians(ctrl1_a)), cy + ctrl_r * math.sin(math.radians(ctrl1_a)))
            mid_pt = QPointF(cx + crest_r * math.cos(mid_rad), cy + crest_r * math.sin(mid_rad))
            path.quadTo(c1, mid_pt)

            c2 = QPointF(cx + ctrl_r * math.cos(math.radians(ctrl2_a)), cy + ctrl_r * math.sin(math.radians(ctrl2_a)))
            ptE_end = QPointF(cx + r_out * math.cos(math.radians(a_out_end)), cy + r_out * math.sin(math.radians(a_out_end)))
            path.quadTo(c2, ptE_end)
        else:
            out_rect = QRectF(cx - r_out, cy - r_out, r_out * 2, r_out * 2)
            path.arcTo(out_rect, -a_out_start, -(a_out_end - a_out_start))

        ptE_ctrl = QPointF(cx + r_out * rad2_x, cy + r_out * rad2_y)
        ptF = QPointF(cx + p_out_start * rad2_x, cy + p_out_start * rad2_y)
        path.quadTo(ptE_ctrl, ptF)

        ptG = QPointF(cx + p_in_start * rad2_x, cy + p_in_start * rad2_y)
        path.lineTo(ptG)

        ptH_ctrl = QPointF(cx + r_in * rad2_x, cy + r_in * rad2_y)
        ptI = QPointF(cx + r_in * math.cos(math.radians(a_in_end)), cy + r_in * math.sin(math.radians(a_in_end)))
        path.quadTo(ptH_ctrl, ptI)

        in_rect = QRectF(cx - r_in, cy - r_in, r_in * 2, r_in * 2)
        path.arcTo(in_rect, -a_in_end, -(a_in_start - a_in_end))

        ptJ_ctrl = QPointF(cx + r_in * rad1_x, cy + r_in * rad1_y)
        path.quadTo(ptJ_ctrl, ptA)
        path.closeSubpath()
        return path

    def get_liquid_slice_path(
        self,
        index: int,
        total_slices: int,
        bulge_r: float = 0.0,
        stretch_angle_deg: float = 0.0,
        gap_angle_deg: float = 3.5,
        wobble: float = 0.0,
        scale: float = 1.0,
        center_offset: Tuple[float, float] = (0.0, 0.0),
        corner_r: float = 8.0
    ) -> QPainterPath:
        """Create a rounded wedge for the primary wheel ring with organic liquid surface tension."""
        if total_slices <= 0 or scale <= 0.05:
            return QPainterPath()

        cx = self.center_x + center_offset[0]
        cy = self.center_y + center_offset[1]

        slice_span = 360.0 / total_slices
        start_angle_deg = -90.0 - (slice_span / 2.0) + index * slice_span

        # Organic liquid tension: base radius lifts by a fraction, crest peaks in center
        r_out = (self.outer_radius + bulge_r * 0.45 + wobble) * scale
        r_in = self.inner_radius * scale
        convex_crest = (bulge_r * 0.65) * scale

        return self.get_annular_sector_path(
            cx, cy, start_angle_deg, start_angle_deg + slice_span,
            r_in, r_out, gap_deg=gap_angle_deg, corner_r=corner_r,
            convex_bulge=convex_crest
        )

    def get_slice_center_point(
        self,
        index: int,
        total_slices: int,
        bulge_r: float = 0.0,
        scale: float = 1.0,
        center_offset: Tuple[float, float] = (0.0, 0.0)
    ) -> QPointF:
        """Get midpoint coordinates of a slice for placing text and icons."""
        slice_span = 360.0 / total_slices
        mid_angle_deg = -90.0 + index * slice_span
        mid_angle_rad = math.radians(mid_angle_deg)
        mid_radius = ((self.inner_radius + self.outer_radius + bulge_r * 0.7) / 2.0) * scale

        cx = self.center_x + center_offset[0]
        cy = self.center_y + center_offset[1]

        x = cx + mid_radius * math.cos(mid_angle_rad)
        y = cy + mid_radius * math.sin(mid_angle_rad)
        return QPointF(x, y)

    def get_sub_tier_params(self, sub_id: str, count: int) -> Tuple[float, float, float, float]:
        """
        Returns (center_angle_deg, total_span_deg, r_in, r_out) for a given sub-menu.
        All angles are in standard polar degrees (-90 = top, 0 = right, 90 = bottom).
        """
        r_in = self.sub_ring_r1
        r_out = self.sub_ring_r2

        if sub_id == 'tools':
            center_angle = 0.0      # Right (TOOLS > slice)
            span = max(140.0, min(180.0, count * 16.4))
        elif sub_id == 'more':
            center_angle = 45.0     # Bottom-Right (MORE > slice)
            span = max(90.0, min(160.0, count * 22.0))
        elif sub_id == 'jpg':
            center_angle = -45.0    # Top-Right (JPG > slice)
            span = max(70.0, count * 22.0)
        elif sub_id == 'pdf':
            center_angle = 90.0     # Bottom (PDF > slice)
            span = max(60.0, count * 24.0)
        elif sub_id == 'webp':
            center_angle = 135.0    # Bottom-Left (WEBP > slice)
            span = max(60.0, count * 24.0)
        else:
            center_angle = 0.0
            span = max(40.0, min(160.0, count * 22.0))

        return center_angle, span, r_in, r_out

    def get_sub_item_path(
        self,
        sub_id: str,
        index: int,
        total_items: int,
        scale: float = 1.0,
        center_offset: Tuple[float, float] = (0.0, 0.0)
    ) -> QPainterPath:
        """Create a curved annular sector path for a sub-menu item in the outer arc tier."""
        if total_items <= 0:
            return QPainterPath()

        center_angle, total_span, r_in, r_out = self.get_sub_tier_params(sub_id, total_items)
        start_angle = center_angle - total_span / 2.0
        step_angle = total_span / total_items

        a1 = start_angle + index * step_angle
        a2 = a1 + step_angle

        cx = self.center_x + center_offset[0]
        cy = self.center_y + center_offset[1]

        cur_r_in = (self.outer_radius + 7.0) * scale
        cur_r_out = cur_r_in + (r_out - r_in) * scale

        return self.get_annular_sector_path(
            cx, cy, a1, a2, cur_r_in, cur_r_out, gap_deg=2.5, corner_r=7.0
        )

    def get_sub_item_center_point(
        self,
        sub_id: str,
        index: int,
        total_items: int,
        scale: float = 1.0,
        center_offset: Tuple[float, float] = (0.0, 0.0)
    ) -> QPointF:
        """Get midpoint coordinates of a sub-menu item for placing icon and text."""
        center_angle, total_span, r_in, r_out = self.get_sub_tier_params(sub_id, total_items)
        start_angle = center_angle - total_span / 2.0
        step_angle = total_span / total_items

        mid_angle_deg = start_angle + (index + 0.5) * step_angle
        mid_angle_rad = math.radians(mid_angle_deg)

        cur_r_in = (self.outer_radius + 7.0) * scale
        cur_r_out = cur_r_in + (r_out - r_in) * scale
        mid_radius = (cur_r_in + cur_r_out) / 2.0

        cx = self.center_x + center_offset[0]
        cy = self.center_y + center_offset[1]

        x = cx + mid_radius * math.cos(mid_angle_rad)
        y = cy + mid_radius * math.sin(mid_angle_rad)
        return QPointF(x, y)

    def hit_test(
        self,
        px: float,
        py: float,
        total_slices: int,
        center_offset: Tuple[float, float] = (0.0, 0.0),
        active_sub_id: Optional[str] = None,
        sub_items_count: int = 0
    ) -> Tuple[Optional[str], Optional[int]]:
        """
        Hit test mouse position against outer concentric radial sub-tier,
        satellite buttons, center hub, inner ring buttons, and outer slices.
        """
        cx = self.center_x + center_offset[0]
        cy = self.center_y + center_offset[1]
        dx = px - cx
        dy = py - cy
        dist = math.sqrt(dx * dx + dy * dy)
        angle = math.degrees(math.atan2(dy, dx))

        # 1. Concentric Radial Sub-Tier (if active)
        if active_sub_id and sub_items_count > 0:
            center_angle, total_span, r_in, r_out = self.get_sub_tier_params(active_sub_id, sub_items_count)
            start_angle = center_angle - total_span / 2.0

            # Inside the curved annular sub-tier
            if r_in - 4.0 <= dist <= r_out + 12.0:
                rel_angle = (angle - start_angle) % 360.0
                if 0.0 <= rel_angle <= total_span:
                    step = total_span / sub_items_count
                    idx = int(rel_angle // step)
                    if 0 <= idx < sub_items_count:
                        return ('sub_item', idx)

            # Bridge corridor between parent wheel rim and sub-tier inner rim
            if self.outer_radius - 8.0 <= dist <= r_in + 4.0:
                rel_angle = (angle - start_angle) % 360.0
                if -8.0 <= rel_angle <= total_span + 8.0:
                    return ('sub_bridge', None)

        # 2. Satellite buttons (top-left shoulder)
        for i in range(len(self.satellite_angles)):
            pos = self.get_satellite_pos(i)
            sx = px - pos.x()
            sy = py - pos.y()
            if sx * sx + sy * sy <= (self.satellite_btn_r + 4.0) ** 2:
                return ('satellite', i)

        # 3. Center hub (with left arrow / right arrow zones)
        if dist <= self.hub_radius:
            if px < cx - 18 and abs(dy) < 26:
                return ('hub_prev', None)
            elif px > cx + 18 and abs(dy) < 26:
                return ('hub_next', None)
            else:
                return ('center', None)

        # 4. Inner ring buttons
        if self.inner_ring_r1 <= dist <= self.inner_ring_r2:
            span = 360.0 / self.inner_button_count
            norm_angle = (angle + 90.0 + span / 2.0) % 360.0
            idx = int(norm_angle // span) % self.inner_button_count
            return ('inner', idx)

        # 5. Outer Ring slices
        if self.inner_radius <= dist <= self.outer_radius + 12.0:
            if total_slices <= 0:
                return (None, None)
            slice_span = 360.0 / total_slices
            norm_angle = (angle + 90.0 + slice_span / 2.0) % 360.0
            idx = int(norm_angle // slice_span) % total_slices
            return ('slice', idx)

        return (None, None)
